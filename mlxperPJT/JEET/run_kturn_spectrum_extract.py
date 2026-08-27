# -*- coding: utf-8 -*-
r"""16k 24 운전점 x 3 모델 --- Jensen 면 + 슬롯 조화 스펙트럼 추출.

한 번의 파싱으로 두 가지를 뽑는다.

  (a) Jensen 면  J(I,b) = 도체별 <|B|^2> / |<B>|^2 의 도체 평균
      --- 앞서 2 운전점에서 잰 것을 격자로 확장 (승인된 제안)
  (b) 슬롯 총 조화 스펙트럼  S_m^t, S_m^r  (면적가중, m=0..12)
      --- 요소 분해 분모를 천이 커널로 재구성할 때 필요.  슬롯 총
      적분은 도체 분할과 무관하므로 6t 것이 전 턴수에 쓰인다.

교정: 앞선 jensen_turn.py 는 앞 25% 블록을 버렸는데 그것은 TS 과도
전제였다.  MS Hybrid 의 블록은 회전자 위치라 전부 유효하다 --- 여기서는
전 블록을 쓴다.

실행 시간 약 1시간 (72파일 x ~340MB 파싱).
산출: map_exports/e10/kturn/kturn_spectrum.json
"""
import gzip
import glob
import io
import json
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.join(HERE, 'map_exports', 'e10', 'kturn')
MODELS = {
    '6t': (r'D:/KangDH/Thesis/e10/_txt_backfill/Ref', '.gz'),
    '4t': (r'G:/KangDH/JEET/kturn_results/kturn4/ACLossCalcExport_kturn4',
           ''),
    '8t': (r'G:/KangDH/JEET/kturn_results/kturn8/ACLossCalcExport_kturn8',
           ''),
}
COND = re.compile(r'(ArmatureSlot\S+|Turn_\S+)\s*$')
TBL = re.compile(r'\s*(\d+)\s+(\d+)\s+(\w+)Table')
BLK = re.compile(r'\s*10\s+Solution\s+(\d+)')
DIR_RE = re.compile(r'Hybrid_Speed_16000RPM_([\d.]+)A_([\d.]+)deg$')
N_HARM = 13


def parse(path):
    """블록별 전 요소 (Bx,By) + 블록1 삼각형/노드/영역."""
    opener = gzip.open if path.endswith('.gz') else io.open
    code2name, xy, tri = {}, {}, []
    BXL, BYL = [], []
    cur, hdr, blk = None, 0, 0
    bx, by = None, None
    with opener(path, 'rt', encoding='utf-8', errors='ignore') as f:
        for line in f:
            mb = BLK.match(line)
            if mb:
                if bx is not None:
                    BXL.append(bx)
                    BYL.append(by)
                blk = int(mb.group(1))
                bx, by = [], []
                cur = None
                continue
            m = TBL.match(line)
            if m:
                cur, hdr = m.group(3), 0
                continue
            if cur is None:
                continue
            hdr += 1
            if hdr <= 3:
                continue
            s = line.strip()
            if not s:
                continue
            if cur == 'Regions' and blk <= 1:
                mm = COND.search(s)
                if mm:
                    code2name[int(s.split(',')[0])] = mm.group(1)
            elif cur == 'Nodes' and blk <= 1:
                p = s.split(',')
                if len(p) >= 3:
                    try:
                        xy[int(p[0])] = (float(p[1]), float(p[2]))
                    except ValueError:
                        pass
            elif cur == 'Elements':
                p = s.split(',')
                if len(p) < 8:
                    continue
                try:
                    if blk <= 1:
                        tri.append((int(p[4]), int(p[1]), int(p[2]),
                                    int(p[3])))
                    bx.append(float(p[5]))
                    by.append(float(p[6]))
                except ValueError:
                    continue
    if bx:
        BXL.append(bx)
        BYL.append(by)
    return code2name, xy, tri, BXL, BYL


def analyse(path):
    code2name, xy, tri, BXL, BYL = parse(path)
    n_el = len(tri)
    idx = np.array([i for i, t in enumerate(tri) if t[0] in code2name])
    codes = np.array([tri[i][0] for i in idx])
    area = np.array([
        abs((xy[tri[i][2]][0] - xy[tri[i][1]][0])
            * (xy[tri[i][3]][1] - xy[tri[i][1]][1])
            - (xy[tri[i][3]][0] - xy[tri[i][1]][0])
            * (xy[tri[i][2]][1] - xy[tri[i][1]][1])) / 2.0
        for i in idx])
    BX = np.array([np.asarray(b)[idx] for b in BXL if len(b) >= n_el])
    BY = np.array([np.asarray(b)[idx] for b in BYL if len(b) >= n_el])

    # 도체의 국소 반경/접선 방향 --- 중심 각도 기준
    cxx, cyy = {}, {}
    for c in np.unique(codes):
        m = codes == c
        a = area[m]
        # 요소 중심
        ex = np.array([(xy[tri[i][1]][0] + xy[tri[i][2]][0]
                        + xy[tri[i][3]][0]) / 3 for i in idx[m]])
        ey = np.array([(xy[tri[i][1]][1] + xy[tri[i][2]][1]
                        + xy[tri[i][3]][1]) / 3 for i in idx[m]])
        cxx[c] = (a * ex).sum() / a.sum()
        cyy[c] = (a * ey).sum() / a.sum()
    th = {c: np.arctan2(cyy[c], cxx[c]) for c in cxx}
    ur = {c: (np.cos(t), np.sin(t)) for c, t in th.items()}

    # (a) Jensen --- 전 블록 평균
    r_list = []
    for c in np.unique(codes):
        m = codes == c
        a = area[m]
        A = a.sum()
        b2 = (BX[:, m] ** 2 + BY[:, m] ** 2)
        j_el = (b2 * a).sum(1) / A
        mbx = (BX[:, m] * a).sum(1) / A
        mby = (BY[:, m] * a).sum(1) / A
        r_list.append(float(j_el.mean()
                            / max((mbx ** 2 + mby ** 2).mean(), 1e-30)))
    jens = np.array(r_list)

    # (b) 슬롯 총 조화 스펙트럼 (면적가중 진폭^2 합, 방향 분리)
    #     각 요소의 (Br, Bt) 시계열 -> rFFT -> |amp|^2 을 면적가중 합산.
    nb = BX.shape[0]
    S_t = np.zeros(N_HARM)
    S_r = np.zeros(N_HARM)
    for c in np.unique(codes):
        m = codes == c
        crx, cry = ur[c]
        Br = BX[:, m] * crx + BY[:, m] * cry
        Bt = -BX[:, m] * cry + BY[:, m] * crx
        for S, B in ((S_r, Br), (S_t, Bt)):
            F = np.fft.rfft(B, axis=0) / nb
            amp2 = np.abs(F) ** 2
            amp2[1:] *= 4.0                      # 단측 -> 피크^2
            n = min(N_HARM, amp2.shape[0])
            S[:n] += (amp2[:n] * area[m]).sum(1)
    return {'n_cond': int(len(np.unique(codes))), 'n_blocks': int(nb),
            'area_mm2': float(area.sum()),
            'jensen_mean': round(float(jens.mean()), 4),
            'jensen_med': round(float(np.median(jens)), 4),
            'S_t': [round(float(v), 6) for v in S_t],
            'S_r': [round(float(v), 6) for v in S_r]}


out = {}
for tag, (root, ext) in MODELS.items():
    dirs = sorted(glob.glob(os.path.join(root, 'Hybrid_Speed_16000RPM_*')))
    rows = []
    for d in dirs:
        m = DIR_RE.search(os.path.basename(d))
        if not m:
            continue
        cur, ph = float(m.group(1)), float(m.group(2))
        if cur < 1.0:
            continue
        f = os.path.join(d, 'FEA_data.txt' + ext)
        if not os.path.exists(f):
            print('누락 %s' % d, flush=True)
            continue
        r = analyse(f)
        r.update({'current_A': cur, 'phase_deg': ph})
        rows.append(r)
        print('%s I=%.1f b=%.0f  J=%.3f  블록 %d' %
              (tag, cur, ph, r['jensen_mean'], r['n_blocks']), flush=True)
    out[tag] = rows
    io.open(os.path.join(SCR, 'kturn_spectrum.json'), 'w',
            encoding='utf-8').write(json.dumps(out, ensure_ascii=False))
print('완료', flush=True)
