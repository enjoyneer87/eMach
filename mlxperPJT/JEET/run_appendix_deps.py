# -*- coding: utf-8 -*-
"""각 부록이 본문에서 몇 번, 무엇을 위해 인용되는가."""
import collections
import io
import re

P = (r'E:\KDH\Overleaf\JEET-2024_rev1\.claude\worktrees\annot-v2'
     r'\JEET_KDH_10p_EN.tex')
L = io.open(P, encoding='utf-8').read().split('\n')
app = next(i for i, l in enumerate(L) if l.strip() == '\\appendix')

TGT = {'sec:appendix_diffusion': 'A', 'fig:eddy_factors': 'A',
       'eq:g_asym': 'A', 'sec:asymptotic': 'A',
       'sec:appendix_variants': 'B', 'fig:hybrid_variants': 'B',
       'eq:2d_diffusion': 'B',
       'sec:appendix_robust': 'C', 'fig:convergence': 'C',
       'fig:ref_ablation': 'C', 'tab:model_form': 'C',
       'tab:extrapolation': 'C'}

cnt = collections.Counter()
print('부록  본문줄  라벨                      문맥')
for i, l in enumerate(L):
    if i >= app:
        break
    for m in re.finditer(r'\\ref\{([^}]+)\}', l):
        k = m.group(1)
        if k in TGT:
            cnt[TGT[k]] += 1
            ctx = re.sub(r'\s+', ' ', l[max(0, m.start() - 78):m.start() + 20])
            print('  %s  L%-5d %-24s %s' % (TGT[k], i + 1, k, ctx[-92:]))
print('\n본문에서 부록으로 가는 참조 수:', dict(cnt))
