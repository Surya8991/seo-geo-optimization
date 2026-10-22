"""Tests for the QA HTTP service (optimizer/service.py).

Each test that talks HTTP starts the real ThreadingHTTPServer on an ephemeral port
in a background thread and shuts it down afterwards. The {"url"} fetch path is
exercised against a second local server, with the private-address guard patched
out for that one test only (the guard itself is tested separately)."""
import http.client
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import qa_check
import service
from test_qa_run import _passing_optimize_html


@pytest.fixture
def server_factory():
    started = []

    def start(token=None):
        srv = service.make_server("127.0.0.1", 0, token=token)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        started.append(srv)
        return srv.server_address[1]

    yield start
    for srv in started:
        srv.shutdown()
        srv.server_close()


def _call(port, method, path, body=None, headers=None, raw=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    hdrs = {"Content-Type": "application/json"}
    hdrs.update(headers or {})
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    conn.request(method, path, body=data, headers=hdrs)
    resp = conn.getresponse()
    payload = json.loads(resp.read().decode())
    conn.close()
    return resp.status, payload


# --- pure helpers -----------------------------------------------------------

def test_parse_requires_exactly_one_source():
    with pytest.raises(service.RequestError):
        service.parse_qa_request({})
    with pytest.raises(service.RequestError):
        service.parse_qa_request({"html": "<p>x</p>", "url": "https://example.com"})


@pytest.mark.parametrize("payload", [
    {"html": "<p>x</p>", "mode": "draft"},
    {"html": "<p>x</p>", "words": True},
    {"html": "<p>x</p>", "words": -5},
    {"html": "<p>x</p>", "keyword": "k" * 500},
    {"html": "   "},
    {"url": 42},
    [],
])
def test_parse_rejects_bad_fields(payload):
    with pytest.raises(service.RequestError) as e:
        service.parse_qa_request(payload)
    assert e.value.status == 400


def test_parse_defaults():
    req = service.parse_qa_request({"html": "<p>x</p>", "keyword": "  "})
    assert req["mode"] == "optimize" and req["keyword"] is None and req["words"] is None


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.1.2.3", "192.168.0.10", "172.16.5.4",
                                "169.254.169.254", "0.0.0.0", "::1", "fe80::1", "::ffff:127.0.0.1",
                                "100.64.0.1", "224.0.0.1"])
def test_blocked_ips(ip):
    assert service.is_blocked_ip(ip)


@pytest.mark.parametrize("ip", ["93.184.216.34", "8.8.8.8", "2606:4700:4700::1111"])
def test_public_ips_allowed(ip):
    assert not service.is_blocked_ip(ip)


def test_check_token():
    assert service.check_token(None, None)
    assert service.check_token("Bearer abc", "abc")
    assert not service.check_token("Bearer abd", "abc")
    assert not service.check_token("abc", "abc")
    assert not service.check_token(None, "abc")


def test_fetch_rejects_non_http_and_private():
    for url in ("file:///etc/passwd", "ftp://example.com/", "http://127.0.0.1/", "http://user:pw@example.com/"):
        with pytest.raises(service.RequestError):
            service.fetch_page(url)


# --- HTTP -------------------------------------------------------------------

def test_health(server_factory):
    port = server_factory()
    status, body = _call(port, "GET", "/health")
    assert status == 200 and body["ok"] is True and body["service"] == "seo-geo-qa"


def test_qa_matches_cli_json(server_factory, tmp_path):
    html = _passing_optimize_html()
    port = server_factory()
    status, body = _call(port, "POST", "/qa", {"html": html, "keyword": "product certification"})
    assert status == 200
    # Same structure as `qa_check --json` for the same page.
    path = tmp_path / "page-green.html"
    path.write_text(html, encoding="utf-8")
    expected = qa_check.evaluate(str(path), keyword="product certification")
    assert set(body) == set(expected) | {"passed"}
    assert body["results"] == expected["results"]
    assert body["passed"] is True
    assert body["mode"] == "optimize"


def test_qa_new_mode_reports_failures(server_factory):
    port = server_factory()
    status, body = _call(port, "POST", "/qa", {"html": "<h1>Hi</h1><p>Short — page.</p>", "mode": "new"})
    assert status == 200
    assert body["mode"] == "new" and body["passed"] is False
    assert any(not r["ok"] for r in body["results"])


def test_bad_requests(server_factory):
    port = server_factory()
    assert _call(port, "POST", "/qa", raw=b"{not json")[0] == 400
    assert _call(port, "POST", "/qa", {"mode": "new"})[0] == 400
    assert _call(port, "POST", "/qa", {"html": "<p>x</p>"}, headers={"Content-Type": "text/plain"})[0] == 415
    assert _call(port, "GET", "/qa")[0] == 405
    assert _call(port, "GET", "/nope")[0] == 404
    assert _call(port, "POST", "/qa", {"url": "http://127.0.0.1:1/"})[0] == 400


def test_body_size_cap(server_factory):
    port = server_factory()
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.putrequest("POST", "/qa")
    conn.putheader("Content-Type", "application/json")
    conn.putheader("Content-Length", str(service.MAX_BODY_BYTES + 1))
    conn.endheaders()  # declare an oversized body but never send it
    resp = conn.getresponse()
    assert resp.status == 413
    conn.close()


def test_bearer_token(server_factory):
    port = server_factory(token="s3cret")
    assert _call(port, "POST", "/qa", {"html": "<p>x</p>"})[0] == 401
    assert _call(port, "POST", "/qa", {"html": "<p>x</p>"}, headers={"Authorization": "Bearer nope"})[0] == 401
    status, body = _call(port, "POST", "/qa", {"html": "<h1>x</h1>"}, headers={"Authorization": "Bearer s3cret"})
    assert status == 200 and "results" in body
    assert _call(port, "GET", "/health")[0] == 200  # health stays open


def test_url_fetch(server_factory, monkeypatch):
    page = _passing_optimize_html().encode("utf-8")

    class Upstream(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/old":
                self.send_response(301)
                self.send_header("Location", "/page")
                self.end_headers()
                return
            if self.path == "/big":
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"x" * (service.MAX_FETCH_BYTES + 10))
                return
            if self.path == "/pdf":
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)

        def log_message(self, *a):
            pass

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
    threading.Thread(target=upstream.serve_forever, daemon=True).start()
    try:
        # Allow loopback for this test only, so the fetch path can run offline.
        monkeypatch.setattr(service, "is_blocked_ip", lambda ip: False)
        up = upstream.server_address[1]
        port = server_factory()
        status, body = _call(port, "POST", "/qa", {"url": f"http://127.0.0.1:{up}/old"})
        assert status == 200 and body["passed"] is True
        assert body["path"].endswith("/old")
        assert _call(port, "POST", "/qa", {"url": f"http://127.0.0.1:{up}/big"})[0] == 502
        assert _call(port, "POST", "/qa", {"url": f"http://127.0.0.1:{up}/pdf"})[0] == 502
    finally:
        upstream.shutdown()
        upstream.server_close()


def test_cli_lists_serve():
    import cli
    assert cli.resolve("serve").endswith("service.py")


# --- live pages (published HTML, no publishing-fields box) -------------------

LIVE_HEAD = ('<html><head><title>Product Certification Guide 2026</title>'
             '<meta content="{desc}" name="description"></head><body>'
             '<h1>Product Certification</h1><p>Short intro.</p></body></html>')


def test_live_meta_helpers():
    desc = "d" * 150
    html = LIVE_HEAD.format(desc=desc)
    assert qa_check.live_head_title(html) == "Product Certification Guide 2026"
    assert qa_check.live_meta_description(html) == desc
    assert qa_check.live_meta_description("<meta name='description' content='x &amp; y'>") == "x & y"
    assert qa_check.live_head_title("<p>no head</p>") is None


def test_live_flag_reads_head_tags(server_factory):
    html = LIVE_HEAD.format(desc="d" * 150)
    port = server_factory()
    _, review = _call(port, "POST", "/qa", {"html": html, "mode": "new"})
    _, live = _call(port, "POST", "/qa", {"html": html, "mode": "new", "live": True})
    labels = lambda body: {r["label"]: r["ok"] for r in body["results"]}  # noqa: E731
    assert labels(review)["Meta title field present"] is False
    assert labels(live)["Meta title <= 60 chars"] is True
    assert "Meta description field present" not in labels(live)
    assert _call(port, "POST", "/qa", {"html": html, "live": "yes"})[0] == 400
