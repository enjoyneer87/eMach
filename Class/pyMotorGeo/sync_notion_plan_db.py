import argparse
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[2]
PLAN_DIR = ROOT / "Plan"

ENTITY_PLAN_L1 = "PLAN_L1"
ENTITY_TASK_L2 = "TASK_L2"
ENTITY_TASK_L3 = "TASK_L3"
ENTITY_ROLE_QUEUE = "ROLE_QUEUE"


@dataclass
class MdInfo:
    path: Path
    rel_path: str
    title: str
    check_total: int
    check_done: int
    has_strike: bool
    strike_samples: List[str]
    section_titles: List[str]


class NotionDBClient:
    def __init__(self, token: str, database_id: str):
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def _request(self, url: str, method: str, payload: Optional[dict] = None) -> dict:
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self.headers, method=method)
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8"))

    def query_all(self, filter_payload: Optional[dict] = None) -> List[dict]:
        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        body: Dict = {"page_size": 100}
        if filter_payload:
            body["filter"] = filter_payload

        results: List[dict] = []
        while True:
            resp = self._request(url, "POST", body)
            results.extend(resp.get("results", []))
            if not resp.get("has_more"):
                break
            body["start_cursor"] = resp.get("next_cursor")
        return results

    def create_page(self, properties: dict) -> dict:
        url = "https://api.notion.com/v1/pages"
        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }
        return self._request(url, "POST", payload)

    def update_page(self, page_id: str, properties: dict) -> dict:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        return self._request(url, "PATCH", {"properties": properties})

    def get_database(self) -> dict:
        url = f"https://api.notion.com/v1/databases/{self.database_id}"
        return self._request(url, "GET")


def parse_markdown(md_path: Path) -> MdInfo:
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    title = md_path.stem
    for ln in lines:
        m = re.match(r"^#\s+(.+)$", ln.strip())
        if m:
            title = m.group(1).strip()
            break

    check_total = 0
    check_done = 0
    has_strike = "~~" in text
    strike_samples: List[str] = []
    section_titles: List[str] = []

    for ln in lines:
        s = ln.strip()
        tm = re.match(r"^-\s*\[([ xX])\]\s+(.+)$", s)
        if tm:
            check_total += 1
            if tm.group(1).lower() == "x":
                check_done += 1

        hm = re.match(r"^##\s+(.+)$", s)
        if hm and len(section_titles) < 20:
            section_titles.append(hm.group(1).strip())

        if "~~" in s and len(strike_samples) < 5:
            strike_samples.append(s[:180])

    rel_path = str(md_path.relative_to(ROOT)).replace("\\", "/")
    return MdInfo(
        path=md_path,
        rel_path=rel_path,
        title=title,
        check_total=check_total,
        check_done=check_done,
        has_strike=has_strike,
        strike_samples=strike_samples,
        section_titles=section_titles,
    )


def list_plan_markdowns() -> List[Path]:
    files = sorted(PLAN_DIR.rglob("*.md"))
    return [p for p in files if p.is_file()]


def task_status_from_checks(total: int, done: int, rel_path: str = "") -> str:
    file_name = Path(rel_path).name if rel_path else ""
    is_action_doc = file_name.startswith("Action")

    if is_action_doc:
        if total == 0:
            return "완료"
        if done < total:
            return "진행 중"
        return "완료"

    if total == 0:
        return "시작 전"
    if done == 0:
        return "시작 전"
    if done < total:
        return "진행 중"
    return "완료"


def notion_now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def plain_text(rich_text_list: List[dict]) -> str:
    if not rich_text_list:
        return ""
    return "".join(rt.get("plain_text", "") for rt in rich_text_list)


def build_properties(
    title: str,
    task_type: str,
    entity_kind: str,
    status: str,
    rel_project_ids: Optional[List[str]],
    attrs: str,
    server_id: str,
    sprint: str,
    priority: str,
    program_tags: List[str],
    available_props: Optional[set] = None,
    available_prop_defs: Optional[dict] = None,
) -> dict:
    def has_prop(name: str) -> bool:
        if available_props is None:
            return True
        return name in available_props

    def prop_type(name: str) -> Optional[str]:
        if not available_prop_defs:
            return None
        p = available_prop_defs.get(name, {})
        return p.get("type")

    def normalize_status_name(value: str) -> str:
        if value.startswith("완료"):
            return "완료"
        return value

    def set_status_property(prop_name: str, value: str) -> None:
        if not has_prop(prop_name):
            return
        ptype = prop_type(prop_name)
        if ptype == "status":
            props[prop_name] = {"status": {"name": value}}
            return
        if ptype == "select":
            props[prop_name] = {"select": {"name": value}}

    def normalize_priority_name(value: str) -> str:
        v = (value or "").strip().upper()
        if v in {"P0", "P1", "P2", "P3"}:
            return v
        if "1" in v:
            return "P1"
        if "2" in v:
            return "P2"
        if "3" in v:
            return "P3"
        if "0" in v:
            return "P0"
        return "P2"

    def select_options(name: str) -> List[str]:
        if not available_prop_defs:
            return []
        p = available_prop_defs.get(name, {})
        opts = p.get("select", {}).get("options", [])
        return [o.get("name", "") for o in opts if o.get("name")]

    props: Dict = {
        "List": {
            "title": [{"type": "text", "text": {"content": title[:180]}}]
        }
    }

    if has_prop("유형"):
        props["유형"] = {"select": {"name": task_type}}
    if has_prop("엔티티구분") and prop_type("엔티티구분") == "select":
        props["엔티티구분"] = {"select": {"name": entity_kind}}

    status_name = normalize_status_name(status)
    if entity_kind == ENTITY_PLAN_L1:
        set_status_property("상태_계획", status_name)
        legacy_status = "진행 중" if status_name == "활성" else "시작 전"
        set_status_property("상태", legacy_status)
    elif entity_kind in {ENTITY_TASK_L2, ENTITY_TASK_L3}:
        set_status_property("상태_작업", status_name)
        set_status_property("상태", status_name)
    elif entity_kind == ENTITY_ROLE_QUEUE:
        set_status_property("상태_역할", status_name)
        set_status_property("상태", "진행 중" if status_name == "진행 중" else "시작 전")
    else:
        set_status_property("상태", status_name)
    if has_prop("주관"):
        props["주관"] = {"select": {"name": "연구실"}}
    if has_prop("우선순위"):
        pr_name = normalize_priority_name(priority)
        options = select_options("우선순위")
        if options and pr_name not in options:
            pr_name = options[0]
        props["우선순위"] = {"select": {"name": pr_name}}
    if has_prop("Program"):
        props["Program"] = {"multi_select": [{"name": t} for t in program_tags]}
    if has_prop("부서"):
        props["부서"] = {
            "rich_text": [{"type": "text", "text": {"content": "MotorAI / Plan Sync"}}]
        }
    if has_prop("열"):
        props["열"] = {
            "rich_text": [{"type": "text", "text": {"content": f"Server:{server_id}"}}]
        }
    if has_prop("속성"):
        props["속성"] = {
            "rich_text": [{"type": "text", "text": {"content": attrs[:1900]}}]
        }
    if has_prop("스프린트"):
        props["스프린트"] = {"multi_select": [{"name": sprint}]}
    if has_prop("착수일"):
        props["착수일"] = {"date": {"start": str(date.today())}}
    if has_prop("동기화일") and prop_type("동기화일") == "date":
        props["동기화일"] = {"date": {"start": notion_now_iso()}}

    if rel_project_ids and has_prop("Project(작업페이지에서 선택)"):
        props["Project(작업페이지에서 선택)"] = {
            "relation": [{"id": rid} for rid in rel_project_ids]
        }
    return props


def upsert_by_title(
    client: NotionDBClient,
    index_by_title: Dict[str, dict],
    properties: dict,
) -> str:
    title_rich = properties["List"]["title"]
    title = title_rich[0]["text"]["content"]
    existing = index_by_title.get(title)
    if existing:
        page_id = existing["id"]
        client.update_page(page_id, properties)
        return page_id

    created = client.create_page(properties)
    return created["id"]


def make_attr_for_md(md: MdInfo, modified_by: str) -> str:
    parts = [
        f"source={md.rel_path}",
        f"check={md.check_done}/{md.check_total}",
    ]
    if md.has_strike:
        parts.append("history=has_strikethrough")
        if md.strike_samples:
            sample = " | ".join(md.strike_samples)
            parts.append(f"samples={sample}")
    parts.append(f"(Modified by Server: {modified_by})")
    return " ; ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Plan markdowns to Notion DB")
    parser.add_argument("--token", default=os.environ.get("NOTION_TOKEN", ""))
    parser.add_argument("--database-id", default=os.environ.get("NOTION_DATABASE_ID", ""))
    parser.add_argument("--server-id", default=os.environ.get("EMACH_SERVER_ID", "38100"))
    parser.add_argument("--sprint", default="스프린트 24")
    args = parser.parse_args()

    if not args.token or not args.database_id:
        raise ValueError("--token and --database-id (or env) are required")

    client = NotionDBClient(args.token, args.database_id)
    db_meta = client.get_database()
    available_prop_defs = db_meta.get("properties", {})
    available_props = set(available_prop_defs.keys())
    if "List" not in available_props:
        raise RuntimeError("Target database must include title property named 'List'")

    existing_pages = client.query_all(
        {
            "property": "List",
            "title": {"contains": "PLANDB | "},
        }
    )
    index_by_title: Dict[str, dict] = {}
    for p in existing_pages:
        title = plain_text(p.get("properties", {}).get("List", {}).get("title", []))
        if title:
            index_by_title[title] = p

    md_files = list_plan_markdowns()
    md_infos = [parse_markdown(p) for p in md_files]

    master_candidates = [
        m for m in md_infos if m.rel_path.endswith("Plan/MotorAI/WBS/03_DevPlan_eMach_Advanced_KO.md")
    ]
    if not master_candidates:
        raise RuntimeError("Master plan markdown not found: 03_DevPlan_eMach_Advanced_KO.md")

    master = master_candidates[0]

    master_title = "PLANDB | L1 | 03_DevPlan_eMach_Advanced_KO"
    master_props = build_properties(
        title=master_title,
        task_type="Project",
        entity_kind=ENTITY_PLAN_L1,
        status="활성",
        rel_project_ids=None,
        attrs=make_attr_for_md(master, args.server_id),
        server_id=args.server_id,
        sprint=args.sprint,
        priority="우선수위1 🔥",
        program_tags=["Python", "VSCODE", "Github"],
        available_props=available_props,
        available_prop_defs=available_prop_defs,
    )
    master_id = upsert_by_title(client, index_by_title, master_props)

    created_or_updated = 1

    for md in md_infos:
        if md.rel_path.endswith("Plan/MotorAI/WBS/03_DevPlan_eMach_Advanced_KO.md"):
            continue

        level2_title = f"PLANDB | L2 | {md.rel_path}"
        props = build_properties(
            title=level2_title,
            task_type="작업",
            entity_kind=ENTITY_TASK_L2,
            status=task_status_from_checks(md.check_total, md.check_done, md.rel_path),
            rel_project_ids=[master_id],
            attrs=make_attr_for_md(md, args.server_id),
            server_id=args.server_id,
            sprint=args.sprint,
            priority="우선순위2",
            program_tags=["Python", "VSCODE", "Github"],
            available_props=available_props,
            available_prop_defs=available_prop_defs,
        )
        file_page_id = upsert_by_title(client, index_by_title, props)
        created_or_updated += 1

    # 최상위 플랜(03)의 ## 섹션을 L3 작업으로 분해하여 실시간 관리 단위를 만듭니다.
    for sec in master.section_titles:
        sec_title = f"PLANDB | L3 | 03::{sec}"
        sec_props = build_properties(
            title=sec_title,
            task_type="작업",
            entity_kind=ENTITY_TASK_L3,
            status="시작 전",
            rel_project_ids=[master_id],
            attrs=f"from=03_DevPlan_eMach_Advanced_KO ; section={sec} ; (Modified by Server: {args.server_id})",
            server_id=args.server_id,
            sprint=args.sprint,
            priority="우선순위2",
            program_tags=["Python", "VSCODE"],
            available_props=available_props,
            available_prop_defs=available_prop_defs,
        )
        upsert_by_title(client, index_by_title, sec_props)
        created_or_updated += 1

    print(f"Plan DB sync complete: {created_or_updated} items upserted")
    print(f"Master page id: {master_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
