from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, Iterable, List


class SlackExport:
    """
    Minimal reader for standard Slack exports:
    - users.json
    - channels.json
    - <channel>/* dated JSON files with arrays of messages
    """

    def __init__(self, root: Path):
        self.root = Path(root)

    def load_users(self) -> List[Dict]:
        return json.loads((self.root / "users.json").read_text(encoding="utf-8"))

    def load_channels(self) -> List[Dict]:
        return json.loads((self.root / "channels.json").read_text(encoding="utf-8"))

    def iter_messages_channel(self, channel_name: str) -> Iterable[Dict]:
        cdir = self.root / channel_name
        if not cdir.exists():
            return
        for p in sorted(cdir.glob("*.json")):
            data = json.loads(p.read_text(encoding="utf-8"))
            for msg in data:
                msg["_channel"] = channel_name
                yield msg

    def iter_messages_all(self) -> Iterable[Dict]:
        # derive channel list from folders to be robust even if channels.json is incomplete
        for cdir in sorted(d for d in self.root.iterdir() if d.is_dir()):
            if cdir.name.startswith("."):  # safety
                continue
            yield from self.iter_messages_channel(cdir.name)

    def count_channel_messages(self, channel_name: str) -> int:
        c = 0
        for _ in self.iter_messages_channel(channel_name):
            c += 1
        return c
