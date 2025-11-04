from pathlib import Path
import json
import typer
from rich import print
from rich.table import Table
from .extract.slack_reader import SlackExport
from .transform.slack_to_html import SlackTransformer
from .load.graph_loader import (
    load_with_mapping,
)

app = typer.Typer(help="Slack → Teams ETL CLI")


@app.command()
def audit(
    export_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True)
):
    sx = SlackExport(export_dir)
    users = sx.load_users()
    channels = sx.load_channels()
    table = Table(title="Slack Export Audit")
    table.add_column("Channel", style="bold")
    table.add_column("Type")
    table.add_column("Members")
    table.add_column("Est. Messages")
    total = 0
    for ch in channels:
        count = sx.count_channel_messages(ch["name"])
        total += count
        table.add_row(
            ch["name"],
            ch.get("is_private") and "private" or "public",
            str(len(ch.get("members", [])) or "-"),
            str(count),
        )
    print(table)
    print(
        f"[green]Users:[/green] {len(users)}   [green]Channels:[/green] {len(channels)}   [green]Messages (est):[/green] {total}"
    )


@app.command("extract-normalized")
def extract_normalized(
    export_dir: Path = typer.Argument(..., exists=True, dir_okay=True),
    out_jsonl: Path = typer.Argument(...),
):
    sx = SlackExport(export_dir)
    users = {u["id"]: u for u in sx.load_users()}
    with out_jsonl.open("w", encoding="utf-8") as w:
        for msg in sx.iter_messages_all():
            uid = msg.get("user") or msg.get("bot_id") or None
            username = (
                users.get(uid, {}).get("profile", {}).get("real_name") if uid else None
            )
            rec = {
                "channel": msg["_channel"],
                "ts": msg.get("ts"),
                "user_id": uid,
                "username": username,
                "text_raw": msg.get("text", ""),
                "files": msg.get("files", []),
                "thread_ts": msg.get("thread_ts"),
                "replies": msg.get("replies", []),
                "subtype": msg.get("subtype"),
            }
            w.write(json.dumps(rec, ensure_ascii=False) + "\\n")
    print(f"[green]Wrote[/green] {out_jsonl}")


@app.command("transform-html")
def transform_html(
    export_dir: Path = typer.Argument(..., exists=True, dir_okay=True),
    in_jsonl: Path = typer.Argument(..., exists=True),
    out_jsonl: Path = typer.Argument(...),
):
    sx = SlackExport(export_dir)
    users = {u["id"]: u for u in sx.load_users()}
    channels_by_id = {c["id"]: c for c in sx.load_channels()}
    xf = SlackTransformer(users=users, channels=channels_by_id)
    with in_jsonl.open("r", encoding="utf-8") as r, out_jsonl.open(
        "w", encoding="utf-8"
    ) as w:
        for line in r:
            rec = json.loads(line)
            html = xf.to_html(rec.get("text_raw", ""))
            rec["text_html"] = html
            w.write(json.dumps(rec, ensure_ascii=False) + "\\n")
    print(f"[green]Wrote[/green] {out_jsonl}")


@app.command("load")
def load(
    mapping: Path = typer.Option(
        ..., exists=True, help="mapping.json: multi-team mapping generated from CSV"
    ),
    messages: Path = typer.Option(
        ..., exists=True, help="Transformed JSONL (with text_html)"
    ),
    rps: float = typer.Option(
        4.0, help="Approx per-channel requests per second (<=5 recommended)."
    ),
    dry_run: bool = typer.Option(True, help="Preview payloads without calling Graph."),
    complete: bool = typer.Option(
        False, help="Complete channel(s) then team(s) after import."
    ),
):
    load_with_mapping(
        mapping_path=mapping,
        messages_path=messages,
        rps=rps,
        dry_run=dry_run,
        complete_when_done=complete,
    )


if __name__ == "__main__":
    app()
