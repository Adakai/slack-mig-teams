from __future__ import annotations
import re
from typing import Dict, Mapping
from markdown_it import MarkdownIt

MENTION_USER = re.compile(r"<@([A-Z0-9]+)>")
MENTION_CHANNEL = re.compile(r"<#([A-Z0-9]+)\|?([^>]+)?>")
LINK_WITH_TEXT = re.compile(r"<(https?://[^|>]+)\|([^>]+)>")
BARE_LINK = re.compile(r"<(https?://[^>]+)>")


class SlackTransformer:
    """
    Converts a subset of Slack mrkdwn to HTML suitable for Teams import.
    - Resolves user mentions (<@U123>) to display names
    - Converts channel mentions (<#C123|name>) to #name text
    - Normalizes <http://|label> and <http://> to markdown links before HTML
    """

    def __init__(self, users: Mapping[str, Dict], channels: Mapping[str, Dict]):
        self.users = users
        self.channels = channels
        self.md = MarkdownIt()  # keep simple; Teams accepts basic HTML

    def _resolve_user(self, m: re.Match) -> str:
        uid = m.group(1)
        name = (
            self.users.get(uid, {}).get("profile", {}).get("real_name")
            or self.users.get(uid, {}).get("name")
            or uid
        )
        return f"@{name}"

    def _resolve_channel(self, m: re.Match) -> str:
        cid = m.group(1)
        explicit = m.group(2)
        name = explicit or self.channels.get(cid, {}).get("name") or cid
        return f"#{name}"

    def preprocess(self, text: str) -> str:
        # Slack’s <> link syntaxes → markdown
        text = LINK_WITH_TEXT.sub(lambda m: f"[{m.group(2)}]({m.group(1)})", text)
        text = BARE_LINK.sub(
            lambda m: f"<{m.group(1)}>", text
        )  # let markdown-it autolink
        # Mentions to plain-text markers so markdown won’t wrap them unexpectedly
        text = MENTION_USER.sub(self._resolve_user, text)
        text = MENTION_CHANNEL.sub(self._resolve_channel, text)
        return text

    def to_html(self, text: str) -> str:
        pre = self.preprocess(text or "")
        return self.md.render(pre)
