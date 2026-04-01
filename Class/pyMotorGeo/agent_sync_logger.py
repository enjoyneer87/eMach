import os
import json
import urllib.request
from typing import Optional

# 민감정보는 코드에 하드코딩하지 않고 환경변수에서만 로드합니다.
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_PAGE_ID = os.environ.get("NOTION_PAGE_ID", "")
SERVER_ID = os.environ.get("EMACH_SERVER_ID", "Local") # 예: 38100, 38101 등 포트번호 지정

class AgentSyncLogger:
    """
    여러 서버와 AI 에이전트 간의 작업 상태를 단일 진실 공급원(Notion)에 실시간으로 기록하고 
    동기화하는 유틸리티 클래스입니다.
    """
    def __init__(self, token: str = NOTION_TOKEN, page_id: str = NOTION_PAGE_ID, server_id: str = SERVER_ID):
        if not token or not page_id:
            raise ValueError(
                "NOTION_TOKEN / NOTION_PAGE_ID 환경변수가 필요합니다."
            )
        self.token = token
        self.page_id = page_id
        self.server_id = server_id
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    def log_event(self, message: str, block_type: str = "paragraph"):
        """단순 텍스트 메시지나 이벤트를 노션에 로깅합니다."""
        url = f"https://api.notion.com/v1/blocks/{self.page_id}/children"
        data = {
            "children": [
                {
                    "object": "block",
                    "type": block_type,
                    block_type: {
                        "rich_text": [{"type": "text", "text": {"content": message}}]
                    }
                }
            ]
        }
        return self._send_request(url, method="PATCH", data=data)

    def log_plan_change(self, old_plan: str, new_plan: str):
        """기존 플랜을 무단으로 삭제하지 않고, 노션의 취소선(strikethrough) 기능과 
           서버 ID(포트번호)를 함께 사용하여 변경 내역을 명확히 추적합니다."""
        url = f"https://api.notion.com/v1/blocks/{self.page_id}/children"
        data = {
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": f"~~{old_plan}~~ "}, "annotations": {"strikethrough": True}},
                            {"type": "text", "text": {"content": f"➡️ {new_plan} "}},
                            {"type": "text", "text": {"content": f"(Modified by Server: {self.server_id})", "link": None}, "annotations": {"italic": True, "color": "gray"}}
                        ]
                    }
                }
            ]
        }
        return self._send_request(url, method="PATCH", data=data)

    def add_task(self, task_name: str, is_completed: bool = False):
        """To-Do 리스트 항목을 노션에 추가(또는 완료 상태로 추가)합니다."""
        
        # 완료된 항목인 경우, 어떤 서버(에이전트)에서 완료했는지 태그를 텍스트에 붙임
        display_text = task_name
        if is_completed:
            display_text += f" (✅ Completed by Server: {self.server_id})"
            
        url = f"https://api.notion.com/v1/blocks/{self.page_id}/children"
        data = {
            "children": [
                {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": display_text}}],
                        "checked": is_completed
                    }
                }
            ]
        }
        return self._send_request(url, method="PATCH", data=data)

    def log_commit_verification(
        self,
        action_id: str,
        task_name: str,
        commit_hash: str,
        commit_subject: str,
    ):
        """Git 커밋을 근거로 Action 완료 로그를 To-Do(checked)로 남깁니다."""
        short_hash = commit_hash[:8]
        line = (
            f"Action {action_id}: {task_name} "
            f"(✅ Verified by commit: {short_hash}, Server: {self.server_id})"
        )
        self.add_task(line, is_completed=True)
        self.log_event(
            f"Commit proof - {short_hash}: {commit_subject}",
            block_type="paragraph",
        )
        
    def send_webhook_log(self, message: str, webhook_url: Optional[str] = None):
        """Discord나 Slack 등의 Webhook URL로 로그를 발송합니다 (옵션)."""
        webhook = webhook_url or os.environ.get("WEBHOOK_URL")
        if not webhook:
            print("Webhook URL이 설정되지 않아 로그만 출력합니다:", message)
            return
            
        data = {"content": message}
        req = urllib.request.Request(
            webhook, 
            data=json.dumps(data).encode("utf-8"), 
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            urllib.request.urlopen(req)
            print("Webhook 전송 성공")
        except Exception as e:
            print(f"Webhook 전송 실패: {e}")

    def _send_request(self, url: str, method: str, data: dict):
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode("utf-8"), 
            headers=self.headers, 
            method=method
        )
        try:
            with urllib.request.urlopen(req) as res:
                return json.loads(res.read().decode("utf-8"))
        except Exception as e:
            if hasattr(e, 'read'):
                error_msg = e.read().decode('utf-8')
                print(f"Notion API Error: {error_msg}")
            else:
                print(f"Request Error: {e}")
            return None

# 간단한 테스트 및 모듈 단위 실행 엔트리포인트
if __name__ == "__main__":
    logger = AgentSyncLogger()
    print("Notion 동기화 테스트 시작...")
    
    # 상태 업데이트 시퀀스 전송
    logger.log_event("🔄 [상태 동기화] agent_sync_logger.py 공통 유틸리티 모듈 적용 완료", "heading_3")
    logger.log_event("이 메시지는 공통 파이썬 모듈 객체를 선언하여 전송되었습니다. 앞으로 모든 서버에서 이 모듈을 import하여 작업 경과를 한 곳에 취합합니다.")
    logger.add_task("[WS-A/WS-D] 로컬 PC 2D Geometry 도면 시각화 Web UI 구축 및 파서 연동", is_completed=True)
    logger.add_task("[WS-A] Pyleecan 연동 브릿지(pyleecan_bridge.py) 작성 및 Export UI 연동", is_completed=False)
    
    print("Notion update completed.")
