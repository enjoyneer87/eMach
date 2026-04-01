import json
import urllib.request

TOKEN = "ntn_f1882298252b4Hmvg4m6xIbT4qIv9wAIZiEDhxOoajQglM"
DB_ID = "33507031-978c-81e5-a8ea-eaf27372f37d"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

PAYLOAD = {
    "properties": {
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
    call(f"https://api.notion.com/v1/databases/{DB_ID}", "PATCH", PAYLOAD)
    db = call(f"https://api.notion.com/v1/databases/{DB_ID}", "GET")
    print("SCHEMA_PATCH=OK")
    for key, value in sorted(db.get("properties", {}).items()):
        print(f"{key}\t{value.get('type')}")


if __name__ == "__main__":
    main()
