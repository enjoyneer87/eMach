import os
import re
import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_PAGE_ID = os.environ.get("NOTION_PAGE_ID", "")
SERVER_ID = os.environ.get("EMACH_SERVER_ID", "Local")

ROOT = Path(__file__).resolve().parents[2]


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _request(url: str, method: str, data: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=_headers(),
        method=method,
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))


def append_blocks(parent_block_id: str, blocks: List[dict]) -> None:
    if not blocks:
        return
    url = f"https://api.notion.com/v1/blocks/{parent_block_id}/children"
    for i in range(0, len(blocks), 80):
        chunk = blocks[i:i + 80]
        _request(url, "PATCH", {"children": chunk})


def rt_text(content: str, *, strikethrough: bool = False, italic: bool = False, color: str = "default") -> dict:
    return {
        "type": "text",
        "text": {"content": content},
        "annotations": {
            "bold": False,
            "italic": italic,
            "strikethrough": strikethrough,
            "underline": False,
            "code": False,
            "color": color,
        },
    }


def parse_strikethrough_rich_text(line: str) -> List[dict]:
    parts: List[dict] = []
    pattern = re.compile(r"~~(.*?)~~")
    last = 0
    for m in pattern.finditer(line):
        if m.start() > last:
            parts.append(rt_text(line[last:m.start()]))
        parts.append(rt_text(m.group(1), strikethrough=True))
        last = m.end()
    if last < len(line):
        parts.append(rt_text(line[last:]))
    if not parts:
        parts = [rt_text(line)]
    return parts


def normalize_title(md_path: Path) -> str:
    name = md_path.stem
    m = re.match(r"^\d+_(.*)$", name)
    if m:
        return m.group(1)
    return name


def parse_markdown(md_path: Path) -> Dict:
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    title = normalize_title(md_path)
    headings: List[str] = []
    todos: List[Tuple[bool, str]] = []
    bullets: List[str] = []

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        hm = re.match(r"^(#{1,6})\s+(.*)$", line)
        if hm:
            level = len(hm.group(1))
            label = hm.group(2).strip()
            if level <= 2:
                headings.append(label)
            continue

        tm = re.match(r"^-\s*\[([ xX])\]\s+(.*)$", line)
        if tm:
            checked = tm.group(1).lower() == "x"
            todos.append((checked, tm.group(2).strip()))
            continue

        if line.startswith("- ") and len(bullets) < 6:
            bullets.append(line[2:].strip())

    if headings:
        title = headings[0]

    return {
        "path": str(md_path.relative_to(ROOT)).replace("\\", "/"),
        "title": title,
        "headings": headings[:8],
        "todos": todos,
        "bullets": bullets,
        "todo_total": len(todos),
        "todo_done": sum(1 for c, _ in todos if c),
    }


def make_file_toggle(parsed: Dict) -> dict:
    summary = f"Tasks {parsed['todo_done']}/{parsed['todo_total']}"
    title = f"{parsed['title']} - {summary}"

    children: List[dict] = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    rt_text(f"Source: {parsed['path']}")
                ]
            },
        }
    ]

    if parsed["headings"]:
        children.append(
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [rt_text("Sections")]
                },
            }
        )
        for h in parsed["headings"][1:6]:
            children.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [rt_text(h)]
                    },
                }
            )

    for item in parsed["bullets"][:4]:
        children.append(
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": parse_strikethrough_rich_text(item)
                },
            }
        )

    for checked, task in parsed["todos"][:30]:
        children.append(
            {
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": parse_strikethrough_rich_text(task),
                    "checked": checked,
                },
            }
        )

    return {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": [rt_text(title)],
            "children": children,
        },
    }


def collect_markdowns() -> List[Path]:
    files = sorted((ROOT / "Plan").rglob("*.md"))
    return [p for p in files if p.is_file()]


def build_hierarchy_blocks() -> List[dict]:
    files = collect_markdowns()
    parsed = [parse_markdown(p) for p in files]

    top_plan = None
    rest = []
    for p in parsed:
        if "03_DevPlan_eMach_Advanced_KO.md" in p["path"]:
            top_plan = p
        else:
            rest.append(p)

    top_children = []
    for item in rest:
        top_children.append(make_file_toggle(item))

    blocks: List[dict] = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    rt_text(
                        f"Plan Sync Snapshot {datetime.now().strftime('%Y-%m-%d %H:%M')} (Server: {SERVER_ID})"
                    )
                ]
            },
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    rt_text("Policy: deleted plan lines stay visible with strikethrough, no hard delete."),
                    rt_text(" Updated by markdown hierarchy sync.", italic=True, color="gray"),
                ]
            },
        },
    ]

    if top_plan is not None:
        top_toggle = make_file_toggle(top_plan)
        # 최상위 계획 아래에 하위 WBS 토글을 배치
        top_toggle["toggle"]["children"].extend(top_children)
        blocks.append(top_toggle)
    else:
        blocks.extend(top_children)

    return blocks


def main() -> int:
    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        raise ValueError("NOTION_TOKEN / NOTION_PAGE_ID 환경변수를 설정하세요.")

    blocks = build_hierarchy_blocks()
    append_blocks(NOTION_PAGE_ID, blocks)
    print(f"Notion hierarchy sync done. blocks={len(blocks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
