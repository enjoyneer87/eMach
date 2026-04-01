#!/usr/bin/env python3
"""
상대 임포트를 절대 임포트로 변경하는 스크립트
from .module -> from module
"""

import re
from pathlib import Path

# pyMotorGeo 디렉토리
pymotorgeo_dir = Path(__file__).parent

# 처리할 파일 목록
py_files = list(pymotorgeo_dir.glob("*.py"))

print(f"처리할 파일 개수: {len(py_files)}")

for filepath in py_files:
    if filepath.name == "fix_imports.py":
        continue
    
    original_content = filepath.read_text(encoding='utf-8')
    modified_content = original_content
    
    # from .module import ... -> from module import ...
    pattern = r'from \.([\w_]+) import'
    if re.search(pattern, modified_content):
        modified_content = re.sub(pattern, r'from \1 import', modified_content)
        print(f"✓ {filepath.name}")
    
    # from . import ... -> from (package) import ... 은 특수 처리 필요
    if 'from . import' in modified_content:
        print(f"⚠ {filepath.name}: 'from . import' 패턴 발견 (수동 처리 필요)")
    
    # 변경이 있으면 저장
    if modified_content != original_content:
        filepath.write_text(modified_content, encoding='utf-8')
        print(f"  → 저장 완료")

print("\n✅ 모든 파일 처리 완료")
