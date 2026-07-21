"""
run_kturn_and_jmag.py
=====================
Kturn AC 손실 해석 + JMAG MS B 추출 런처.

사용법:
    python run_kturn_and_jmag.py              # 둘 다 동시 실행 (기존 동작)
    python run_kturn_and_jmag.py --jmag-only  # JMAG(MATLAB)만
    python run_kturn_and_jmag.py --kturn-only # Kturn(Motor-CAD)만

⚠️ 동시 실행은 Motor-CAD 와 MATLAB 이 같은 PC 자원을 함께 쓴다.
   한쪽이 이미 돌고 있으면 --jmag-only / --kturn-only 로 분리 실행할 것.

⚠️ Kturn 쪽은 run_kturn_full.bat 을 호출하는데, 이 .bat 은 마지막 줄이 `pause` 라
   비대화형 셸에서는 영구 대기한다. 터미널에서 직접 띄울 때만 사용할 것.
   백그라운드 실행이 필요하면 run_kturn_pipeline.py 를 직접 호출하라
   (4턴/8턴은 전류 격자가 다르므로 반드시 2회 분리 호출).
"""
import subprocess
import sys
import os
import threading
from pathlib import Path

# ─── 경로 설정 ───────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
PYTHON_EXE = r"C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\python.exe"

KTURN_BAT   = SCRIPT_DIR / "run_kturn_full.bat"
# MATLAB 버전: 2026-07-20 R2025a → R2026a 로 변경 (사용자 지정).
# 다른 버전으로 되돌리려면 아래 경로만 수정.
MATLAB_EXE  = r"C:\Program Files\MATLAB\R2026a\bin\matlab.exe"
JMAG_SCRIPT = SCRIPT_DIR / "Other" / "devSurfInterp4HYBMS.m"
# 2026-07-20 정정: 기존 값 E:\KDH\e10\MSConductorModel\e10MS_ConductorModel_SCL_Load~13
#   → 존재하지 않는 경로였음(Case* 하위폴더 구조 아님). 실제 데이터는 아래 경로에
#   평면(flat) 구조로 있고, 케이스 번호는 파일명에 들어감:
#     e10MS_ConductorModel_SCL_Load~13_Case{1..30}_MagB_wireTable.mat
#   출처: "J:\내 드라이브\EveryMotor_JEET_data\SESSION_HANDOFF_2026-07-17.md" (83~86행)
JMAG_WORKDIR = r"D:\KangDH\Emlab_emach\mlxperPJT\JEET"

# devSurfInterp4HYBMS.m 이 쓰는 커스텀 함수(findMatFiles, len, greyColor,
# mkdelauyTByPartTable, plotCircle, reduceWidthpolar, getdeluayInterpPointValue)는
# 전부 D:\KangDH\Emlab_emach\tools\ 하위에 있으므로 path 추가가 필수다.
MATLAB_TOOLS = r"D:\KangDH\Emlab_emach\tools"

MATLAB_CMD = (
    f"addpath(genpath('{MATLAB_TOOLS}')); "
    f"cd('{JMAG_WORKDIR}'); "
    f"run('{str(JMAG_SCRIPT).replace(chr(92), '/')}'); "
    f"exit;"
)

# ─── 로그 헬퍼 ───────────────────────────────────────────────────────────────
def stream_output(proc, prefix):
    for line in iter(proc.stdout.readline, b""):
        print(f"[{prefix}] {line.decode('utf-8', errors='replace').rstrip()}", flush=True)
    proc.stdout.close()


# ─── Kturn 실행 ──────────────────────────────────────────────────────────────
def run_kturn():
    print(f"\n{'='*60}")
    print(f"[KTURN] 시작: {KTURN_BAT}")
    print(f"{'='*60}\n")

    if not KTURN_BAT.exists():
        print(f"[KTURN] ERROR: 파일 없음 → {KTURN_BAT}")
        return 1

    proc = subprocess.Popen(
        ["cmd", "/c", str(KTURN_BAT)],
        cwd=str(SCRIPT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stream_output(proc, "KTURN")
    ret = proc.wait()
    print(f"\n[KTURN] 완료 (exit code={ret})")
    return ret


# ─── JMAG (MATLAB batch) 실행 ────────────────────────────────────────────────
def run_jmag():
    print(f"\n{'='*60}")
    print(f"[JMAG]  MATLAB batch 시작")
    print(f"  workdir : {JMAG_WORKDIR}")
    print(f"  script  : {JMAG_SCRIPT}")
    print(f"{'='*60}")
    print("  [!] 실행 전 확인 (2026-07-20 미해결):")
    print("      devSurfInterp4HYBMS.m 18행 필터가 주석 처리돼 있어 대상이 60개가 된다.")
    print("      그중 30개는 이미 처리된 산출물(*DenseFitwithDT.mat)이며 WireTable 이")
    print("      없어 28행 height(WireTable) 에서 오류로 죽는다.")
    print("      → 18행 주석을 해제하면 30개(입력만)로 좁혀진다.")
    print("      → 산출물 30개가 이미 있으므로 재실행이 필요한지 먼저 판단할 것.\n")

    if not Path(MATLAB_EXE).exists():
        print(f"[JMAG] ERROR: MATLAB 없음 → {MATLAB_EXE}")
        return 1
    if not JMAG_SCRIPT.exists():
        print(f"[JMAG] ERROR: 스크립트 없음 → {JMAG_SCRIPT}")
        return 1
    if not Path(JMAG_WORKDIR).exists():
        print(f"[JMAG] ERROR: JMAG 데이터 폴더 없음 → {JMAG_WORKDIR}")
        return 1

    proc = subprocess.Popen(
        [MATLAB_EXE, "-batch", MATLAB_CMD],
        cwd=JMAG_WORKDIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stream_output(proc, "JMAG ")
    ret = proc.wait()
    print(f"\n[JMAG] 완료 (exit code={ret})")
    return ret


# ─── 메인 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # cp949 콘솔에서 비ASCII(이모지 등) 출력 시 UnicodeEncodeError 방지
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    USAGE = (
        "usage: python run_kturn_and_jmag.py [--jmag-only | --kturn-only]\n"
        "  (no flag)     : run both concurrently\n"
        "  --jmag-only   : MATLAB/JMAG only\n"
        "  --kturn-only  : Motor-CAD/Kturn only"
    )

    flags = set(a.lower() for a in sys.argv[1:])
    unknown = flags - {"--jmag-only", "--kturn-only"}
    if unknown:
        print(f"[error] unknown argument(s): {sorted(unknown)}")
        print(USAGE)
        sys.exit(2)
    if {"--jmag-only", "--kturn-only"} <= flags:
        print("[error] --jmag-only and --kturn-only are mutually exclusive")
        print(USAGE)
        sys.exit(2)

    do_kturn = "--jmag-only" not in flags
    do_jmag = "--kturn-only" not in flags

    mode = "Kturn + JMAG 동시" if (do_kturn and do_jmag) else ("Kturn 전용" if do_kturn else "JMAG 전용")
    print(f"실행 모드: {mode}")
    print(f"Python: {sys.executable}")
    print(f"MATLAB: {MATLAB_EXE}")

    threads = []
    if do_kturn:
        threads.append(threading.Thread(target=run_kturn, name="kturn"))
    if do_jmag:
        threads.append(threading.Thread(target=run_jmag, name="jmag"))

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("\n" + "="*60)
    print("모든 작업 완료!")
    print("="*60)
