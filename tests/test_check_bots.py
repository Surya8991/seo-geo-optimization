"""Tests for robots.txt parsing / retrieval-bot access (optimizer/check_bots.py)."""
import check_bots


def test_robots_url_from_base():
    assert check_bots.robots_url("https://www.example.com/") == "https://www.example.com/robots.txt"
    assert check_bots.robots_url("example.com") == "https://example.com/robots.txt"


def test_specific_agent_block():
    robots = """
User-agent: PerplexityBot
Disallow: /

User-agent: *
Disallow:
"""
    groups = check_bots.parse_robots(robots)
    assert check_bots.agent_can_fetch(groups, "PerplexityBot", "/") is False
    assert check_bots.agent_can_fetch(groups, "OAI-SearchBot", "/") is True  # falls back to *


def test_wildcard_block_catches_retrieval_bots():
    robots = "User-agent: *\nDisallow: /\n"
    groups = check_bots.parse_robots(robots)
    assert check_bots.agent_can_fetch(groups, "ChatGPT-User", "/") is False


def test_allow_overrides_disallow_by_longest_match():
    robots = "User-agent: *\nDisallow: /\nAllow: /blog\n"
    groups = check_bots.parse_robots(robots)
    assert check_bots.agent_can_fetch(groups, "any", "/blog/post") is True
    assert check_bots.agent_can_fetch(groups, "any", "/private") is False


def test_empty_robots_allows_all():
    groups = check_bots.parse_robots("")
    assert check_bots.agent_can_fetch(groups, "OAI-SearchBot", "/") is True


def test_multiple_user_agents_share_a_block():
    robots = "User-agent: GPTBot\nUser-agent: CCBot\nDisallow: /\n"
    groups = check_bots.parse_robots(robots)
    assert check_bots.agent_can_fetch(groups, "GPTBot", "/") is False
    assert check_bots.agent_can_fetch(groups, "CCBot", "/") is False
