# -*- coding: utf-8 -*-
"""Fig 1 (``fig2_<model>_ts_vs_2d.png``) 용 슬롯-1 축약본을 만든다 --- 출처 단계.

``plot_fig2_kernel_comparison`` 은 Motor-CAD 전 주기 export 4개
(Ref/SC 의 TS-FEA + MS-FEA, 합계 1.386 GB)를 읽지만, 실제로 건드리는 것은
**슬롯 1 주변의 작은 창** 뿐이다. 이 스크립트는 그 창만 잘라 npz 4개
(합계 ~640 kB)로 굽는다. 배포 레포는 원본 txt 대신 이 npz 를 싣는다.

무엇을 남기는가
---------------
* 요소: 슬롯 1 도체 bbox 를 슬롯 로컬 좌표에서 ``--margin-mm`` (기본 4 mm)
  만큼 넓힌 창 안의 요소 + 도체 요소 전부. 창은 ``_slot_frame(domain='slot')``
  의 여유 1.5 mm 와 ``conductor_je_2d``/``conductor_je_strips`` 의 보간
  반경 6 mm 를 모두 덮는다.
* 블록: ``--every`` (기본 4) 간격으로 128 중 32 블록. 그림이 쓰는 것과 같다.
* 블록별 배열: TS 는 ``je_am2``, MS 는 ``bx``/``by``/``a_wbm``.
* **블록별 RegionsTable 의 Jval 은 반드시 같이 남긴다.** ``conductor_je_2d``
  는 ``i_net_a=None`` 이면 ``p['jval'][code]`` 로 순전류를 되찾는데, 이걸
  빼면 kernel_2d 가 조용히 0.05% 어긋난다.
* 정적 기하: ``reg``/``x_mm``/``y_mm``/``area_mm2``/``tri``/``node_xy``/
  영역 이름·sigma. 블록마다 같은지 검사하고, 다르면 실패한다.

읽는 쪽
-------
``field_metrics.iter_mes_blocks`` 가 ``.npz`` 를 알아본다. 따라서
``plot_fig2_kernel_comparison`` 은 고칠 것이 없다.

쓰는 법
-------
    python run_cut_fig1_slot_reduction.py                # Ref + SC
    python run_cut_fig1_slot_reduction.py --model Ref --dry-run
    JEET_DATA_ROOT=... python run_cut_fig1_slot_reduction.py

1.4 GB 를 통째로 읽지 않고 한 줄씩 흘려보내므로 메모리는 블록 하나
(~3 MB) 뿐이고, 4개 합쳐 30초 안팎이다. 이 스크립트는 원본 txt 가 있는
저자 기계 전용이다 --- 배포 레포는 산출물만 쓴다.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from jeet_acloss_rbf.field_metrics import (            # noqa: E402
    REDUCTION_FORMAT, _build_block_dict, _parse_regions,
    slot_conductor_codes)

# 데이터 루트는 JEET_DATA_ROOT 로 덮어쓸 수 있다 (배포 레포/CI 용).
_DATA = os.environ.get('JEET_DATA_ROOT',
                       os.path.join(HERE, 'map_exports', 'e10'))

MARGIN_MM = 4.0                      # 도체 bbox 바깥 여유 (슬롯 로컬 좌표)
# 역할별로 남길 블록별 요소 배열. TS 는 실측 Je, MS 는 커널의 여기(勵磁).
ROLE_FIELDS = {'TS': ('je_am2',), 'MS': ('bx', 'by', 'a_wbm')}

# _locate_blocks 와 같은 관례 --- 블록 머리와 표 머리를 같은 정규식으로 판다.
_SOL_RE = re.compile(r"^\s*\d+\s+Solution\s+\d+(.*)$")
_TBL_RE = re.compile(r"^\s*\d+\s+(\d+)\s+(\w+Table)")

_STATIC_KEYS = ('reg', 'x_mm', 'y_mm', 'area_mm2', 'tri', 'node_xy')


def load_kernel_dim_study():
    """SOURCES/SLOT/EVERY 를 run_kernel_dim_study.py 에서 그대로 가져온다.

    같은 상수를 두 벌 두면 언젠가 갈라진다. 파일 경로로 싣는 이유는
    run_fig1_shared_scale.py 와 같다 (JEET 폴더는 패키지가 아니다).
    """
    spec = importlib.util.spec_from_file_location(
        "kds", os.path.join(HERE, "run_kernel_dim_study.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def stream_blocks(path, every, stats):
    """``(bi-1) % every == 0`` 인 Solution 블록의 원문 줄만 흘려보낸다.

    파일을 통째로 읽지 않는다 --- 400 MB export 하나가 줄 리스트로는 수 GB
    가 되기 때문. ``stats['n_solution_blocks']`` 에 파일 전체 블록 수를
    채워 준다(원본의 ``p['n_solution_blocks']`` 를 보존하기 위함).
    """
    bi = 0
    buf = None
    with open(path, encoding='utf-8', errors='ignore') as fh:
        for ln in fh:
            if _SOL_RE.match(ln):
                if buf is not None:
                    yield bi, buf
                    buf = None
                bi += 1
                if (bi - 1) % every == 0:
                    buf = [ln]
                continue
            if buf is not None:
                buf.append(ln)
    if buf is not None:
        yield bi, buf
    stats['n_solution_blocks'] = bi


def block_dict(lines, path):
    """블록 하나의 원문 줄을 ``iter_mes_blocks`` 와 같은 dict 로 만든다.

    RegionsTable 은 **그 블록 것**을 쓴다 --- 회전각마다 상전류가 달라
    첫 블록 것을 재사용하면 jval 의 부호까지 틀어진다(field_metrics 주석).
    """
    tables = {}
    for i, ln in enumerate(lines):
        mt = _TBL_RE.match(ln)
        if mt:
            n, name = int(mt.group(1)), mt.group(2)
            if name not in tables:
                tables[name] = (i + 1, n)
    if 'RegionsTable' not in tables:
        raise ValueError('블록에 RegionsTable 이 없다 --- 블록별 jval 을 '
                         '얻을 수 없다: %s' % path)
    deg = re.search(r"Rotate Step\s*(-?[0-9.]+)",
                    _SOL_RE.match(lines[0]).group(1))
    blk = {'rotate_deg': float(deg.group(1)) if deg else 0.0,
           'tables': tables}
    names, jval, sigma = _parse_regions(lines, tables['RegionsTable'])
    # n_solution_blocks 는 파일을 다 흘려본 뒤에야 알 수 있어 여기서는 0.
    return _build_block_dict(lines, blk, names, jval, sigma, path, 0)


def slot_window_mask(p, slot_id, margin_mm=MARGIN_MM):
    """슬롯 로컬 좌표에서 도체 bbox + margin 안의 요소 마스크.

    도체 요소는 창 밖으로 나가더라도 무조건 남긴다(개구부에 잘린 바 대비).
    """
    cm = np.isin(p['reg'], list(slot_conductor_codes(p, slot_id)))
    if not cm.any():
        raise ValueError('슬롯 %d 도체 요소를 찾지 못했다' % slot_id)
    xc, yc = p['x_mm'][cm], p['y_mm'][cm]
    ang = np.arctan2(yc.mean(), xc.mean())
    c, s = np.cos(-ang), np.sin(-ang)
    R = np.array([[c, -s], [s, c]])
    pr = np.column_stack([p['x_mm'], p['y_mm']]) @ R.T
    pc = pr[cm]
    win = ((pr[:, 0] >= pc[:, 0].min() - margin_mm)
           & (pr[:, 0] <= pc[:, 0].max() + margin_mm)
           & (pr[:, 1] >= pc[:, 1].min() - margin_mm)
           & (pr[:, 1] <= pc[:, 1].max() + margin_mm))
    return win | cm


def reduce_block(p, keep, fields):
    """마스크 ``keep`` 으로 요소를 자르고 절점 색인을 조밀하게 다시 매긴다.

    ``np.unique`` 가 오름차순이라 재색인은 단조다 --- 삼각형·절점의 순서가
    원본과 같게 유지되고, 따라서 tricontourf 결과도 그대로다.
    """
    tri = p['tri'][keep]
    ids = np.unique(tri.ravel())
    remap = np.full(int(ids.max()) + 1, -1, np.int64)
    remap[ids] = np.arange(ids.size)
    out = {'reg': p['reg'][keep].astype(np.int32),
           'x_mm': p['x_mm'][keep], 'y_mm': p['y_mm'][keep],
           'area_mm2': p['area_mm2'][keep],
           'tri': remap[tri].astype(np.int32),
           'node_xy': p['node_xy'][ids],
           'rotate_deg': p['rotate_deg'],
           'names': p['names'], 'jval': p['jval'], 'sigma': p['sigma']}
    for k in fields:
        out[k] = np.asarray(p[k], np.float64)[keep]
    return out


def _same(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return a.shape == b.shape and np.array_equal(a, b, equal_nan=True)


def cut(path, role, out_npz, slot_id=1, every=4, margin_mm=MARGIN_MM,
        verbose=True):
    """export 하나를 축약해 npz 로 굽는다. 반환: 요약 dict."""
    fields = ROLE_FIELDS[role]
    stats = {'n_solution_blocks': 0}
    t0 = time.time()
    steps, per_block, ref, n_src = [], [], None, 0
    for bi, lines in stream_blocks(path, every, stats):
        p = block_dict(lines, path)
        keep = slot_window_mask(p, slot_id, margin_mm)
        r = reduce_block(p, keep, fields)
        if ref is None:
            ref, n_src = r, int(keep.size)
        else:
            for k in _STATIC_KEYS:
                if not _same(ref[k], r[k]):
                    raise ValueError(
                        '블록 %d 의 정적 기하 %r 가 블록 %d 와 다르다 --- '
                        '스텝마다 메시를 다시 만든 export 라 축약본 한 벌로 '
                        '표현할 수 없다: %s' % (bi, k, steps[0], path))
            if ref['names'] != r['names'] or ref['sigma'] != r['sigma']:
                raise ValueError('블록 %d 에서 RegionsTable 의 이름/sigma 가 '
                                 '바뀌었다: %s' % (bi, path))
        steps.append(bi)
        per_block.append(r)
    if not steps:
        raise ValueError('Solution 블록을 하나도 읽지 못했다: %s' % path)

    codes = sorted(ref['names'])
    d = {'format': REDUCTION_FORMAT,
         'source_name': os.path.basename(path),
         'n_solution_blocks': np.int64(stats['n_solution_blocks']),
         'every': np.int64(every), 'slot_id': np.int64(slot_id),
         'margin_mm': np.float64(margin_mm),
         'steps': np.asarray(steps, np.int32),
         'rotate_deg': np.asarray([r['rotate_deg'] for r in per_block],
                                  np.float64),
         'name_codes': np.asarray(codes, np.int32),
         'name_names': np.asarray([ref['names'][c] for c in codes]),
         'sigma_vals': np.asarray([ref['sigma'].get(c, np.nan)
                                   for c in codes], np.float64),
         # 블록별 Jval --- conductor_je_2d 의 i_net 되찾기용. 빼면 안 된다.
         'jval': np.asarray([[r['jval'].get(c, np.nan) for c in codes]
                             for r in per_block], np.float64),
         'elem_fields': np.asarray(list(fields))}
    for k in _STATIC_KEYS:
        d[k] = ref[k]
    for k in fields:
        d[k] = np.stack([r[k] for r in per_block])

    os.makedirs(os.path.dirname(os.path.abspath(out_npz)), exist_ok=True)
    np.savez_compressed(out_npz, **d)
    info = {'out': out_npz, 'bytes': os.path.getsize(out_npz),
            'n_blocks': len(steps), 'n_elem': int(ref['reg'].size),
            'n_elem_src': n_src, 'sec': time.time() - t0,
            'src_bytes': os.path.getsize(path)}
    if verbose:
        print('  %-3s %5d/%5d elem  %2d blk  %8.1f kB  (%.0f s)  <- %s'
              % (role, info['n_elem'], info['n_elem_src'], info['n_blocks'],
                 info['bytes'] / 1024.0, info['sec'],
                 os.path.basename(path)))
    return info


def reduced_paths(data_root, tag):
    """모델 태그 하나의 (TS, MS) 축약본 경로."""
    d = os.path.join(data_root, 'fields', 'reduced')
    return (os.path.join(d, 'slotcut_%s_TS.npz' % tag),
            os.path.join(d, 'slotcut_%s_MS.npz' % tag))


def main(argv=None) -> int:
    kds = load_kernel_dim_study()
    ap = argparse.ArgumentParser(
        description='Fig 1 용 슬롯-1 축약 npz 생성 (원본 txt 필요)')
    ap.add_argument('--model', nargs='+', default=['Ref', 'SC'],
                    choices=sorted(kds.SOURCES),
                    help='축약할 모델 (기본: Ref SC)')
    ap.add_argument('--data-root', default=_DATA,
                    help='map_exports/e10 루트 (기본: JEET_DATA_ROOT, '
                         '없으면 스크립트 옆 map_exports/e10)')
    ap.add_argument('--out-dir', default=None,
                    help='산출 폴더 (기본: <data-root>/fields/reduced)')
    ap.add_argument('--slot', type=int, default=kds.SLOT)
    ap.add_argument('--every', type=int, default=kds.EVERY)
    ap.add_argument('--margin-mm', type=float, default=MARGIN_MM)
    ap.add_argument('--dry-run', action='store_true',
                    help='입력 존재 여부와 산출 경로만 확인')
    a = ap.parse_args(argv)

    total_in = total_out = 0
    for model in a.model:
        ts, hy, tag = kds.SOURCES[model][:3]
        outs = reduced_paths(a.data_root, tag)
        if a.out_dir:
            outs = tuple(os.path.join(a.out_dir, os.path.basename(o))
                         for o in outs)
        print('=== %s (slot %d, every %d, margin %.1f mm)'
              % (model, a.slot, a.every, a.margin_mm))
        for src, role, out in zip((ts, hy), ('TS', 'MS'), outs):
            if not os.path.exists(src):
                raise SystemExit('원본 export 가 없다: %s' % src)
            if a.dry_run:
                print('  %-3s %s\n      -> %s' % (role, src, out))
                continue
            info = cut(src, role, out, slot_id=a.slot, every=a.every,
                       margin_mm=a.margin_mm)
            total_in += info['src_bytes']
            total_out += info['bytes']
    if not a.dry_run and total_out:
        print('합계 %.3f GB -> %.1f kB (%.0f 배 축소)'
              % (total_in / 1e9, total_out / 1024.0, total_in / total_out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
