import json
import os
import urllib.request

TOKEN = os.environ.get("NOTION_TOKEN", "")
DB_ID = os.environ.get("NOTION_DATABASE_ID", "")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

PAYLOAD = {
    "properties": {
        "엔티티구분": {
            "select": {
                "options": [
                    {"name": "PLAN_L1", "color": "purple"},
                    {"name": "TASK_L2", "color": "blue"},
                    {"name": "TASK_L3", "color": "green"},
                    {"name": "ROLE_QUEUE", "color": "orange"},
                ]
            }
        },
        "역할": {
            "select": {
                "options": [
                    {"name": "PM-TRIAGE", "color": "purple"},
                    {"name": "IMPLEMENTER", "color": "blue"},
                    {"name": "REVIEWER", "color": "green"},
                    {"name": "INTEGRATOR", "color": "orange"},
                    {"name": "DOCS-SYNC", "color": "gray"},
                ]
            }
        },
        "상태_계획": {
            "select": {
                "options": [
                    {"name": "초안", "color": "default"},
                    {"name": "활성", "color": "blue"},
                    {"name": "동결", "color": "yellow"},
                    {"name": "아카이브", "color": "gray"},
                ]
            }
        },
        "상태_작업": {
            "select": {
                "options": [
                    {"name": "시작 전", "color": "default"},
                    {"name": "진행 중", "color": "blue"},
                    {"name": "완료", "color": "green"},
                    {"name": "홀드", "color": "yellow"},
                ]
            }
        },
        "상태_역할": {
            "select": {
                "options": [
                    {"name": "대기", "color": "default"},
                    {"name": "진행 중", "color": "blue"},
                    {"name": "리뷰대기", "color": "purple"},
                    {"name": "완료", "color": "green"},
                    {"name": "홀드", "color": "yellow"},
                ]
            }
        },
        "서버ID": {"rich_text": {}},
        "작업키": {"rich_text": {}},
        "우선순위": {
            "select": {
                "options": [
                    {"name": "P0", "color": "red"},
                    {"name": "P1", "color": "orange"},
                    {"name": "P2", "color": "yellow"},
                    {"name": "P3", "color": "gray"},
                ]
            }
        },
        "소스경로": {"rich_text": {}},
        "커밋해시": {"rich_text": {}},
        "완료근거": {"url": {}},
        "부모": {"relation": {"database_id": DB_ID, "single_property": {}}},
        "검증완료": {"checkbox": {}},
        "동기화일": {"date": {}},
        "비고": {"rich_text": {}},
    }
}


def call(url: str, method: str, payload=None):
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode("utf-8"))


def main():
    if not TOKEN or not DB_ID:
        raise ValueError("NOTION_TOKEN and NOTION_DATABASE_ID must be set")

    call(f"https://api.notion.com/v1/databases/{DB_ID}", "PATCH", PAYLOAD)
    db = call(f"https://api.notion.com/v1/databases/{DB_ID}", "GET")
    print("SCHEMA_PATCH=OK")
    for key, value in sorted(db.get("properties", {}).items()):
        print(f"{key}\t{value.get('type')}")


if __name__ == "__main__":
    main()
