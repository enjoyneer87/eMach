function run_gen_kturn()
% run_gen_kturn  e10 헤어핀 턴수 변형 .mot 생성기(gen_e10_hairpin_turns.py) 실행 래퍼
% =========================================================================
% 목적
%   Ref(6턴, e10Turn6V261.mot) 기반으로 4턴/8턴 헤어핀 .mot 파일을 자동 생성한다.
%   생성 스크립트는 Motor-CAD ActiveX(win32com)로 GUI를 띄워 동작하므로,
%   MATLAB in-process(pyrunfile)가 아니라 "독립 Python 프로세스"로 실행한다.
%   (COM/GUI 앱이 MATLAB 세션을 불안정하게 만드는 것을 방지)
%
% 사전 조건
%   1. Motor-CAD가 설치/라이선스 활성 상태여야 함 (COM: MotorCAD.AppAutomation)
%   2. pywin32(win32com)가 설치된 Python 인터프리터가 필요함.
%      사용 환경: pyMotorEnv_310 가상환경 (Python 3.10.11)
%        C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\python.exe
%        - pywin32 311 (win32com OK) → 이 스크립트의 raw COM Dispatch 동작
%        - ansys-motorcad-core 0.8.4 (from ansys.motorcad.core import MotorCAD)
%      ※ PATH 1순위 python(JMAG의 python3.8)에는 win32com이 없으므로 사용 불가.
%      ※ 대안: C:\Program Files\Python38\python.exe 에도 win32com 있음(pymotorcad 없음).
%   3. 기준 파일 존재: D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot
%
% 생성 결과 (스크립트 내부 OUT_DIR 기준)
%   D:\KangDH\Thesis\e10\refModel\e10Turn4V261.mot
%   D:\KangDH\Thesis\e10\refModel\e10Turn8V261.mot
%
% 사용법
%   >> run_gen_kturn          % 기본 인터프리터로 실행
%
% 참고: 생성 대상 턴수/경로를 바꾸려면 gen_e10_hairpin_turns.py 상단의
%       TARGET_TURNS / MOT_BASE / OUT_DIR 를 직접 수정.
% =========================================================================

    % --- pywin32(win32com)가 설치된 Python 인터프리터 (pyMotorEnv_310 venv) ---
    PYEXE = 'C:\Users\user\.ansys_python_venvs\pyMotorEnv_310\Scripts\python.exe';

    % --- 실행할 스크립트(이 .m 파일과 같은 폴더) ---
    here   = fileparts(mfilename('fullpath'));
    script = fullfile(here, 'gen_e10_hairpin_turns.py');

    % --- 사전 점검 ---
    assert(isfile(PYEXE),  'Python 인터프리터를 찾을 수 없음: %s', PYEXE);
    assert(isfile(script), '생성 스크립트를 찾을 수 없음: %s', script);

    baseMot = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot';
    if ~isfile(baseMot)
        warning('기준 .mot 파일이 없음: %s\n(스크립트 MOT_BASE 경로를 확인하세요)', baseMot);
    end

    % win32com 사용 가능 여부 확인
    [okChk, ~] = system(sprintf('"%s" -c "import win32com.client"', PYEXE));
    if okChk ~= 0
        error(['선택한 Python에 win32com(pywin32)이 없습니다: %s\n', ...
               'pywin32가 설치된 인터프리터로 PYEXE를 바꾸거나 `pip install pywin32` 하세요.'], PYEXE);
    end

    % --- 실행 (독립 프로세스, 콘솔 출력 실시간 표시: '-u' = unbuffered) ---
    cmd = sprintf('"%s" -u "%s"', PYEXE, script);
    fprintf('[run_gen_kturn] 실행: %s\n', cmd);
    status = system(cmd);   % 출력은 MATLAB 명령창으로 스트리밍됨

    if status ~= 0
        error('gen_e10_hairpin_turns.py 실행 실패 (exit code %d). 위 로그를 확인하세요.', status);
    end

    % --- 결과 확인 ---
    outDir   = 'D:\KangDH\Thesis\e10\refModel';
    expected = {'e10Turn4V261.mot', 'e10Turn8V261.mot'};
    fprintf('\n[run_gen_kturn] 생성 결과 확인:\n');
    for k = 1:numel(expected)
        f = fullfile(outDir, expected{k});
        if isfile(f)
            d = dir(f);
            fprintf('   ✓ %s  (%.1f KB)\n', f, d.bytes/1024);
        else
            fprintf('   ✗ %s  (생성 안 됨)\n', f);
        end
    end

    fprintf(['\n다음 단계:\n', ...
        '  1. Motor-CAD에서 4/8턴 .mot 열어 슬롯 geometry 육안 확인\n', ...
        '     (특히 헤어핀 도체 높이/배열이 의도대로 반영됐는지)\n', ...
        '  2. gen_e10_satumap_from_mot.m 를 각 .mot에 적용해 SatuMap 생성\n', ...
        '  3. AC 손실 LAB 시뮬레이션 → RBF 학습용 Kturn 데이터 확보\n']);
end
