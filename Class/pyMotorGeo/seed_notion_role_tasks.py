import argparse
import json
import urllib.request
from typing import Dict, List, Optional


def req(url: str, headers: dict, method: str = "GET", payload: Optional[dict] = None) -> dict:
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, headers=headers, method=method, data=data)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def query_by_title(db_id: str, headers: dict, keyword: str) -> List[dict]:
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    body = {
        "filter": {
            "property": "List",
            "title": {"contains": keyword},
        },
        "page_size": 100,
    }
    return req(url, headers, "POST", body).get("results", [])


def upsert_row(db_id: str, headers: dict, title: str, props: dict) -> str:
    exists = query_by_title(db_id, headers, title)
    exact = None
    for row in exists:
        rtitle = ""
        t = row.get("properties", {}).get("List", {}).get("title", [])
        if t:
            rtitle = "".join(x.get("plain_text", "") for x in t)
        if rtitle == title:
            exact = row
            break

    properties = {
        "List": {"title": [{"type": "text", "text": {"content": title}}]},
    }
    properties.update(props)

    if exact:
        req(f"https://api.notion.com/v1/pages/{exact['id']}", headers, "PATCH", {"properties": properties})
        return exact["id"]

    created = req(
        "https://api.notion.com/v1/pages",
        headers,
        "POST",
        {
            "parent": {"database_id": db_id},
            "properties": properties,
        },
    )
    return created["id"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed role-separated collaboration rows in Notion DB")
    parser.add_argument("--token", required=True)
    parser.add_argument("--db-id", required=True)
    parser.add_argument("--server-id", default="38100")
    args = parser.parse_args()

    headers = {
        "Authorization": f"Bearer {args.token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    master_rows = query_by_title(args.db_id, headers, "PLANDB | L1 | 03_DevPlan_eMach_Advanced_KO")
    parent_rel = []
    if master_rows:
        parent_rel = [{"id": master_rows[0]["id"]}]

    role_rows = [
        {
            "title": "ROLE | PM-TRIAGE | Intake Queue",
            "role": "PM-TRIAGE",
            "status": "진행 중",
            "priority": "P0",
            "task_key": "ROLE-PM",
            "note": "작업키 부여/중복 방지/우선순위 지정",
        },
        {
            "title": "ROLE | IMPLEMENTER | Build Queue",
            "role": "IMPLEMENTER",
            "status": "시작 전",
            "priority": "P1",
            "task_key": "ROLE-IMPL",
            "note": "코드 구현 + 테스트 + 커밋",
        },
        {
            "title": "ROLE | REVIEWER | Validation Queue",
            "role": "REVIEWER",
            "status": "시작 전",
            "priority": "P1",
            "task_key": "ROLE-REV",
            "note": "리스크/회귀/품질 검증",
        },
        {
            "title": "ROLE | INTEGRATOR | Merge Queue",
            "role": "INTEGRATOR",
            "status": "시작 전",
            "priority": "P1",
            "task_key": "ROLE-INT",
            "note": "브랜치 통합 + 충돌해결 + 릴리즈 준비",
        },
        {
            "title": "ROLE | DOCS-SYNC | Notion Queue",
            "role": "DOCS-SYNC",
            "status": "시작 전",
            "priority": "P2",
            "task_key": "ROLE-DOC",
            "note": "Notion 상태 갱신 + 커밋 근거 링크 반영",
        },
    ]

    for row in role_rows:
        props = {
            "역할": {"select": {"name": row["role"]}},
            "상태": {"status": {"name": row["status"]}},
            "우선순위": {"select": {"name": row["priority"]}},
            "서버ID": {"rich_text": [{"type": "text", "text": {"content": args.server_id}}]},
            "작업키": {"rich_text": [{"type": "text", "text": {"content": row["task_key"]}}]},
            "비고": {"rich_text": [{"type": "text", "text": {"content": row["note"]}}]},
            "검증완료": {"checkbox": False},
        }
        if parent_rel:
            props["부모"] = {"relation": parent_rel}
        upsert_row(args.db_id, headers, row["title"], props)

    print("ROLE_SEED=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
