#!/usr/bin/env python3
"""
Retrieval-bot access check: fetch the site's robots.txt and report whether the AI
RETRIEVAL/search bots (the ones that build answers and citations) are allowed. If
these are blocked, the page cannot be cited no matter how well it is optimized.

Retrieval bots (must be allowed to be cited): OAI-SearchBot, ChatGPT-User,
PerplexityBot, Claude-Web / Claude-SearchBot, Google-Extended is a TRAINING bot and
reported separately (blocking it does not affect citations).

Domain/base_url come from config.json.

Usage:
    python optimizer/check_bots.py                 # uses base_url from config.json
    python optimizer/check_bots.py https://foo.com # override the site
"""
import sys
import urllib.request
import urllib.error

from config_loader import CONFIG

RETRIEVAL_BOTS = ["OAI-SearchBot", "ChatGPT-User", "PerplexityBot",
                  "Claude-Web", "Claude-SearchBot", "Google"]
TRAINING_BOTS = ["GPTBot", "Google-Extended", "CCBot", "anthropic-ai", "ClaudeBot"]


def parse_robots(text):
    """Parse robots.txt into {user_agent_lower: [(kind, path), ...]} where kind is
    'allow' or 'disallow'. A block can list several User-agent lines; rules apply to
    all of them until the next User-agent line starts a new block."""
    groups = {}
    current = []           # user-agents this block applies to
    starting_block = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, value = line.split(":", 1)
        field = field.strip().lower()
        value = value.strip()
        if field == "user-agent":
            if not starting_block:   # a User-agent after rules starts a fresh block
                current = []
            current.append(value.lower())
            groups.setdefault(value.lower(), [])
            starting_block = True
        elif field in ("allow", "disallow"):
            starting_block = False
            for ua in current:
                groups.setdefault(ua, []).append((field, value))
    return groups


def agent_can_fetch(groups, agent, path="/"):
    """Longest-match Allow/Disallow decision for `agent` on `path`. Unknown agent
    falls back to the '*' group. Absent/empty -> allowed."""
    rules = groups.get(agent.lower())
    if rules is None:
        rules = groups.get("*", [])
    best_kind, best_len = None, -1
    for kind, pattern in rules:
        if pattern == "":
            # "Disallow:" (empty) means allow all; "Allow:" empty is ignored.
            if kind == "disallow" and best_len < 0:
                best_kind, best_len = "allow", 0
            continue
        if path.startswith(pattern) and len(pattern) > best_len:
            best_kind, best_len = kind, len(pattern)
    return best_kind != "disallow"   # default allow when no rule matches


def robots_url(base_url):
    from urllib.parse import urlparse
    p = urlparse(base_url if "://" in base_url else "https://" + base_url)
    return f"{p.scheme}://{p.netloc}/robots.txt"


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "seo-geo-bot-check/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def report(groups):
    print("\nRETRIEVAL / search bots (MUST be allowed to be cited):")
    ok = True
    for bot in RETRIEVAL_BOTS:
        allowed = agent_can_fetch(groups, bot, "/")
        ok = ok and allowed
        print(f"  [{'OK  ' if allowed else 'BLOCKED'}] {bot}")
    print("\nTRAINING bots (blocking these does NOT affect citations; your call):")
    for bot in TRAINING_BOTS:
        allowed = agent_can_fetch(groups, bot, "/")
        print(f"  [{'allowed' if allowed else 'blocked'}] {bot}")
    star = agent_can_fetch(groups, "*", "/")
    print(f"\nDefault (*) can fetch '/': {'yes' if star else 'NO (blanket block, check this)'}")
    if not ok:
        print("\nWARNING: at least one retrieval bot is blocked; the page cannot be cited by it.")
    return 0 if ok else 1


def main(base_url):
    url = robots_url(base_url)
    print(f"Fetching {url} ...")
    try:
        text = fetch(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("No robots.txt (404): everything is allowed by default. OK.")
            return 0
        print(f"HTTP error {e.code} fetching robots.txt.")
        return 1
    except Exception as e:
        print(f"Could not fetch robots.txt: {e}")
        return 1
    return report(parse_robots(text))


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else CONFIG["base_url"]
    sys.exit(main(base))
