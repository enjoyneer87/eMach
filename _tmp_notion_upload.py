import os
import sys

# 테스트할 현재 서버 ID(RDP 포트 번호 모방)를 환경변수에 등록
os.environ['EMACH_SERVER_ID'] = '38100'
sys.path.insert(0, r'D:\KangDH\Emlab_emach\Class\pyMotorGeo')

from agent_sync_logger import AgentSyncLogger
logger = AgentSyncLogger()

# 1. 문서 헤더 업데이트
logger.log_event('🔥 대시보드 리뉴얼: 통합 개발 플랜 (Action 12)', 'heading_2')
logger.log_event('단일 노션 페이지를 SSOT로 사용하여 에이전트들이 처리한 To-Do 목록과 담당 서버 포트번호(예: 38100)를 실시간 태깅합니다.', 'paragraph')

# 2. Action 12 항목들을 노션에 To-Do로 일괄 적재
actions = [
    'benchmark 10케이스 ID와 데이터 위치 동결 (계획)',
    'Contract v1 스키마 및 파서 UI 연동',
    'pyMCAD h5/txt 입력 표준화 모듈 (수행 대기)',
    'MLDataset payload validator',
    'Streamlit 2D Geometry 도면 정밀 렌더링(Arc/Circle) 패치',
    'Pyleecan / Motor-CAD 형상 Export 브릿지 구축 (Next Step)',
]

# 이미 저희가 같이 수행했던 내용들은 True로 설정
completed_indexes = [2, 4, 5] 

for idx, action in enumerate(actions, start=1):
    is_done = idx in completed_indexes
    logger.add_task(f'Action {idx}. {action}', is_completed=is_done)

print('노션 대시보드 리뉴얼 및 서버 ID 태깅(38100) 업로드 완료!')
