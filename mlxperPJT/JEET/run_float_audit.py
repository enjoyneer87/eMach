# -*- coding: utf-8 -*-
"""[13:27] 키워드·표 규모, [14:07] 그림/표가 참조에서 몇 쪽 떨어지는가."""
import io
import re

W = r'E:\KDH\Overleaf\JEET-2024_rev1\.claude\worktrees\annot-v2'
TEX = io.open(W + r'\JEET_KDH_10p_EN.tex', encoding='utf-8').read()
AUX = io.open(W + r'\JEET_KDH_10p_EN.aux', encoding='utf-8').read()
L = TEX.split('\n')

# ── 라벨 -> (번호, 쪽) ────────────────────────────────────────────────
page = {}
for m in re.finditer(r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{(\d+)\}', AUX):
    page[m.group(1)] = (m.group(2), int(m.group(3)))

# ── 본문 줄 -> 쪽 (라벨 위치를 앵커로 선형 근사가 아니라, 참조가 있는
#    줄이 속한 절의 라벨 쪽을 쓴다) ─────────────────────────────────
anchors = sorted((i, page[m.group(1)][1])
                 for i, l in enumerate(L)
                 for m in [re.search(r'\\label\{(sec:[^}]+)\}', l)]
                 if m and m.group(1) in page)


def line_page(i):
    p = None
    for j, pg in anchors:
        if j <= i:
            p = pg
        else:
            break
    return p


print('=== [13:27] 키워드')
k = re.search(r'\\keywords\{(.*?)\}\s*$', TEX, re.S | re.M)
if not k:
    k = re.search(r'\\keywords\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', TEX)
kw = [x.strip() for x in re.split(r'\\and|,', k.group(1))] if k else []
print('  개수 %d' % len(kw))
for x in kw:
    print('   -', re.sub(r'\s+', ' ', x)[:70])

print('\n=== [13:27] 표 규모')
for m in re.finditer(r'\\begin\{table\*?\}(.*?)\\end\{table\*?\}', TEX, re.S):
    b = m.group(1)
    lab = re.search(r'\\label\{([^}]+)\}', b)
    lab = lab.group(1) if lab else '?'
    rows = b.count('\\\\')
    cols = 0
    cs = re.search(r'\\begin\{tabular\}\{([^}]*)\}', b)
    if cs:
        cols = len(re.findall(r'[lcrp]', cs.group(1)))
    n, pg = page.get(lab, ('?', 0))
    print('  Table %-3s p%-3s %-22s %2d행 %2d열  각주 %d행'
          % (n, pg, lab[:22], rows, cols, b.count('$\\dagger$')
             + b.count('$\\ddagger$') + b.count('\\P')))

print('\n=== [14:07] float 이 첫 참조에서 몇 쪽 떨어지나')
print('  %-26s %5s %5s %6s  %s' % ('label', 'float', 'ref', 'delta', 'kind'))
for lab, (n, pg) in sorted(page.items(), key=lambda kv: kv[1][1]):
    if not (lab.startswith('fig:') or lab.startswith('tab:')
            or lab.startswith('Compare')):
        continue
    first = None
    for i, l in enumerate(L):
        if re.search(r'\\ref\{' + re.escape(lab) + r'\}', l):
            first = line_page(i)
            break
    if first is None:
        print('  %-26s %5d %5s %6s  참조 없음' % (lab[:26], pg, '-', '-'))
        continue
    d = pg - first
    flag = '  <-- 앞섬' if d < 0 else ('  <-- %d쪽 뒤' % d if d > 1 else '')
    print('  %-26s %5d %5d %6s  %s%s'
          % (lab[:26], pg, first, ('%+d' % d), 'Fig' if lab.startswith('fig') else 'Tab',
             flag))
