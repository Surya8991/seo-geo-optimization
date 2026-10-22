#!/usr/bin/env python3
"""
Tiny HTTP front end for the QA gate, so another app (e.g. a dashboard that tracks
AI visibility) can score a page without shelling out. Standard library only.

    seo-geo serve                          # 127.0.0.1:8765
    seo-geo serve --host 0.0.0.0 --port 9000

Endpoints:
    GET  /health  -> {"ok": true, "service": "seo-geo-qa", "version": ...}
    POST /qa      -> body {"html": "<...>"} or {"url": "https://..."}, plus optional
                     "keyword" (str), "mode" ("optimize" | "new", default "optimize"),
                     "words" (int, advisory) and "live" (bool; default true for {url}):
                     a live page's meta title/description are read from its <title> and
                     <meta name="description"> instead of the review-copy publishing box.
                     Returns exactly what `qa_check.py --json` prints (report + "passed").

Safety:
- Optional bearer token: set SEO_GEO_SERVICE_TOKEN and every /qa call must send
  `Authorization: Bearer <token>` (constant-time compare). /health stays open.
- Request bodies are capped (MAX_BODY_BYTES) and must declare Content-Length.
- {"url"} fetches are http(s) only, time-limited, size-capped, follow at most a few
  redirects, and refuse any host that resolves to a private, loopback, link-local,
  multicast or otherwise reserved address. The connection is pinned to the address
  that was checked, so a DNS answer cannot change between the check and the fetch.
- Input is only ever parsed as HTML text. Nothing from a request is executed,
  written to disk, or used to build a file path.

Brand settings come from config.json like every other script, falling back to the
committed config.example.json in a fresh checkout.
"""
import argparse
import hmac
import http.client
import ipaddress
import json
import os
import socket
import ssl
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urljoin, urlsplit

try:
    import qa_check
except ImportError:
    from optimizer import qa_check

SERVICE_NAME = "seo-geo-qa"
VERSION = "1"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
TOKEN_ENV = "SEO_GEO_SERVICE_TOKEN"

MAX_BODY_BYTES = 2 * 1024 * 1024     # incoming JSON request body
MAX_FETCH_BYTES = 3 * 1024 * 1024    # fetched page body for {"url"} requests
FETCH_TIMEOUT = 10.0                 # seconds, whole fetch (connect + all reads)
MAX_REDIRECTS = 3
MAX_KEYWORD_LEN = 200
MAX_URL_LEN = 2048
MODES = ("optimize", "new")
HTML_TYPES = ("text/html", "application/xhtml+xml", "text/plain")


class RequestError(Exception):
    """A client-visible error: HTTP status + short message (never a traceback)."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


# ---------------------------------------------------------------------------
# Input validation (pure, unit-tested)
# ---------------------------------------------------------------------------

def parse_qa_request(payload):
    """Validate a decoded /qa JSON body. Returns a normalized dict with exactly one
    of html/url plus keyword, mode, words. Raises RequestError(400) on bad input."""
    if not isinstance(payload, dict):
        raise RequestError(400, "body must be a JSON object")
    html, url = payload.get("html"), payload.get("url")
    if (html is None) == (url is None):
        raise RequestError(400, "send exactly one of 'html' or 'url'")
    if html is not None and (not isinstance(html, str) or not html.strip()):
        raise RequestError(400, "'html' must be a non-empty string")
    if url is not None and (not isinstance(url, str) or not url.strip() or len(url) > MAX_URL_LEN):
        raise RequestError(400, "'url' must be a non-empty string")

    mode = payload.get("mode", "optimize")
    if mode not in MODES:
        raise RequestError(400, "'mode' must be 'optimize' or 'new'")

    keyword = payload.get("keyword")
    if keyword is not None:
        if not isinstance(keyword, str) or len(keyword) > MAX_KEYWORD_LEN:
            raise RequestError(400, f"'keyword' must be a string of at most {MAX_KEYWORD_LEN} chars")
        keyword = keyword.strip() or None

    words = payload.get("words")
    if words is not None:
        # bool is an int subclass; reject it explicitly
        if isinstance(words, bool) or not isinstance(words, int) or not 0 < words < 1_000_000:
            raise RequestError(400, "'words' must be a positive integer")

    live = payload.get("live", url is not None)
    if not isinstance(live, bool):
        raise RequestError(400, "'live' must be true or false")

    return {"html": html, "url": url.strip() if url else None,
            "keyword": keyword, "mode": mode, "words": words, "live": live}


def is_blocked_ip(ip):
    """True for any address a server-side fetch must never reach."""
    addr = ipaddress.ip_address(ip)
    if isinstance(addr, ipaddress.IPv6Address) and addr.ipv4_mapped:
        addr = addr.ipv4_mapped
    return (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast
            or addr.is_reserved or addr.is_unspecified or not addr.is_global)


def check_token(header_value, expected):
    """Constant-time bearer check. No expected token configured = open."""
    if not expected:
        return True
    if not header_value or not header_value.startswith("Bearer "):
        return False
    return hmac.compare_digest(header_value[len("Bearer "):].strip().encode(), expected.encode())


# ---------------------------------------------------------------------------
# Safe fetch for {"url"} requests
# ---------------------------------------------------------------------------

def _resolve_public(host, port):
    """Resolve `host` and return one address, refusing if ANY answer is non-public
    (a split answer is a classic rebinding trick)."""
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise RequestError(502, f"could not resolve host: {host}") from e
    addrs = [info[4][0] for info in infos]
    if not addrs:
        raise RequestError(502, f"could not resolve host: {host}")
    for a in addrs:
        if is_blocked_ip(a.split("%")[0]):
            raise RequestError(400, "url resolves to a private or reserved address")
    return addrs[0]


class _PinnedHTTPConnection(http.client.HTTPConnection):
    def __init__(self, host, port, ip, timeout):
        super().__init__(host, port, timeout=timeout)
        self._ip = ip

    def connect(self):
        self.sock = socket.create_connection((self._ip, self.port), self.timeout)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host, port, ip, timeout):
        super().__init__(host, port, timeout=timeout, context=ssl.create_default_context())
        self._ip = ip

    def connect(self):
        sock = socket.create_connection((self._ip, self.port), self.timeout)
        # SNI + certificate verification still use the real hostname.
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def fetch_page(url, timeout=FETCH_TIMEOUT, max_bytes=MAX_FETCH_BYTES):
    """GET an http(s) page with SSRF guards. Returns the decoded HTML text."""
    deadline = time.monotonic() + timeout
    for _ in range(MAX_REDIRECTS + 1):
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise RequestError(400, "url must be an absolute http(s) URL")
        if parts.username or parts.password:
            raise RequestError(400, "url must not contain credentials")
        try:
            port = parts.port or (443 if parts.scheme == "https" else 80)
        except ValueError as e:
            raise RequestError(400, "url has an invalid port") from e
        ip = _resolve_public(parts.hostname, port)
        remaining = max(0.5, deadline - time.monotonic())
        conn_cls = _PinnedHTTPSConnection if parts.scheme == "https" else _PinnedHTTPConnection
        conn = conn_cls(parts.hostname, port, ip, remaining)
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        try:
            conn.request("GET", path, headers={
                "User-Agent": f"{SERVICE_NAME}/{VERSION}",
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1",
                "Accept-Encoding": "identity",
            })
            resp = conn.getresponse()
            if resp.status in (301, 302, 303, 307, 308):
                loc = resp.getheader("Location")
                if not loc:
                    raise RequestError(502, "redirect without a Location header")
                url = urljoin(url, loc)
                continue
            if resp.status != 200:
                raise RequestError(502, f"upstream returned HTTP {resp.status}")
            ctype = (resp.getheader("Content-Type") or "").lower()
            if ctype and not any(t in ctype for t in HTML_TYPES):
                raise RequestError(502, f"upstream is not HTML ({ctype.split(';')[0]})")
            declared = resp.getheader("Content-Length")
            if declared and declared.isdigit() and int(declared) > max_bytes:
                raise RequestError(502, "upstream page is too large")
            chunks, size = [], 0
            while True:
                if time.monotonic() > deadline:
                    raise RequestError(504, "upstream fetch timed out")
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise RequestError(502, "upstream page is too large")
                chunks.append(chunk)
            charset = "utf-8"
            if "charset=" in ctype:
                charset = ctype.split("charset=", 1)[1].split(";")[0].strip().strip('"') or "utf-8"
            try:
                return b"".join(chunks).decode(charset, errors="replace")
            except LookupError:
                return b"".join(chunks).decode("utf-8", errors="replace")
        except (socket.timeout, TimeoutError) as e:
            raise RequestError(504, "upstream fetch timed out") from e
        except (OSError, http.client.HTTPException) as e:
            raise RequestError(502, f"upstream fetch failed: {type(e).__name__}") from e
        finally:
            conn.close()
    raise RequestError(502, "too many redirects")


def run_qa(req):
    """Score a validated request. Same shape as `qa_check.py --json`."""
    html = req["html"] if req["html"] is not None else fetch_page(req["url"])
    report = qa_check.evaluate_html(
        html, forced_words=req["words"], is_new=req["mode"] == "new",
        keyword=req["keyword"], path=req["url"] or "<html>", live=req.get("live", False))
    report["passed"] = all(r["ok"] for r in report["results"])
    return report


# ---------------------------------------------------------------------------
# HTTP plumbing
# ---------------------------------------------------------------------------

class QAHandler(BaseHTTPRequestHandler):
    server_version = f"{SERVICE_NAME}/{VERSION}"
    sys_version = ""
    timeout = 30  # per-socket-op: a stalled client cannot pin a worker thread forever

    def _send(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):  # one terse line, never request bodies
        sys.stderr.write(f"[{SERVICE_NAME}] {self.address_string()} {fmt % args}\n")

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/health":
            self._send(200, {"ok": True, "service": SERVICE_NAME, "version": VERSION})
        elif path == "/qa":
            self._send(405, {"error": "use POST"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path == "/health":
            self._send(405, {"error": "use GET"})
            return
        if path != "/qa":
            self._send(404, {"error": "not found"})
            return
        try:
            if not check_token(self.headers.get("Authorization"), self.server.token):
                raise RequestError(401, "missing or invalid bearer token")
            ctype = (self.headers.get("Content-Type") or "").lower()
            if "json" not in ctype:
                raise RequestError(415, "Content-Type must be application/json")
            length = self.headers.get("Content-Length")
            if length is None or not length.isdigit():
                raise RequestError(411, "Content-Length required")
            if int(length) > MAX_BODY_BYTES:
                raise RequestError(413, f"body exceeds {MAX_BODY_BYTES} bytes")
            raw = self.rfile.read(int(length))
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                raise RequestError(400, "body is not valid JSON") from e
            self._send(200, run_qa(parse_qa_request(payload)))
        except RequestError as e:
            self.close_connection = True  # the body may be unread; do not reuse the socket
            self._send(e.status, {"error": e.message})
        except Exception as e:  # noqa: BLE001 - never leak a traceback to the client
            sys.stderr.write(f"[{SERVICE_NAME}] internal error: {type(e).__name__}: {e}\n")
            self._send(500, {"error": "internal error"})

    def do_PUT(self):
        self._send(405, {"error": "method not allowed"})

    do_DELETE = do_PATCH = do_PUT


def make_server(host=DEFAULT_HOST, port=DEFAULT_PORT, token=None):
    """Build (not start) the server. port=0 picks a free port (tests)."""
    server = ThreadingHTTPServer((host, port), QAHandler)
    server.daemon_threads = True
    server.token = token if token is not None else os.environ.get(TOKEN_ENV) or None
    return server


def main(argv=None):
    ap = argparse.ArgumentParser(description="HTTP service for the QA gate (GET /health, POST /qa).")
    ap.add_argument("--host", default=DEFAULT_HOST, help=f"bind address (default {DEFAULT_HOST})")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port (default {DEFAULT_PORT})")
    a = ap.parse_args(argv)
    server = make_server(a.host, a.port)
    host, port = server.server_address[:2]
    auth = "bearer token required" if server.token else f"no auth (set {TOKEN_ENV} to require a token)"
    print(f"{SERVICE_NAME} listening on http://{host}:{port}  ({auth})", flush=True)
    if not server.token and a.host not in ("127.0.0.1", "localhost", "::1"):
        print(f"warning: bound to {a.host} without {TOKEN_ENV}; anyone who can reach it can use it",
              file=sys.stderr, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
