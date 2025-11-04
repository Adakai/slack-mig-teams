import csv
import json
import sys
import pathlib

in_csv = pathlib.Path(sys.argv[1])
out_json = pathlib.Path(sys.argv[2])

teams = {}
with in_csv.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        slack = (row.get("slack_channel") or "").strip()
        team = (row.get("team") or "").strip()
        chan = (row.get("channel") or "").strip()
        mtype = (row.get("membership_type") or "standard").strip().lower()
        archive = (row.get("archive") or "").strip().upper() == "Y"
        share_with_raw = (row.get("share_with") or "").strip()
        share_with = (
            [s.strip() for s in share_with_raw.split(";") if s.strip()]
            if share_with_raw
            else []
        )

        if not (slack and team and chan):
            continue
        teams.setdefault(team, []).append(
            {
                "slack": slack,
                "channel": chan,
                "type": mtype,
                "archive": archive,
                "share_with": share_with,
            }
        )

mapping = {"teams": teams}
out_json.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {out_json}")
