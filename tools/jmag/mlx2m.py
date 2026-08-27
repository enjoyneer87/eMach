# -*- coding: utf-8 -*-
"""MLX(라이브 스크립트) 코드 추출기.

.mlx 는 OPC ZIP 컨테이너다.  matlab/document.xml 안에 코드가
<w:t> 텍스트 노드로 들어 있다.  코드만 뽑아 평문으로 낸다.

사용: python mlx_read.py <파일.mlx> [줄수]
"""
import re
import sys
import zipfile


def mlx_code(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('matlab/document.xml').decode('utf-8')
    # 문단 단위로 자르고, 각 문단의 텍스트 노드를 이어붙인다
    out = []
    for para in re.findall(r'<w:p(?: [^>]*)?>(.*?)</w:p>', xml, re.S):
        is_code = 'w:val="code"' in para[:200]
        txt = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', para, re.S))
        txt = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', txt, flags=re.S)
        txt = (txt.replace('&lt;', '<').replace('&gt;', '>')
               .replace('&amp;', '&').replace('&quot;', '"')
               .replace('&#39;', "'"))
        if txt.strip():
            out.append(txt if is_code else '%% [텍스트] ' + txt)
    return '\n'.join(out)


if __name__ == '__main__':
    p = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 6
    code = mlx_code(p)
    lines = code.split('\n')
    print('\n'.join(lines[:n]))
    if len(lines) > n:
        print('... (전체 %d줄)' % len(lines))
