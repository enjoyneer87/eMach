%% runAFCustomLossLab.m
% AF Factor → Motor-CAD Lab Custom Link(.txt) + Internal Custom Loss 적용 (단계별)
%
% 워크플로우 (셀 단위로 실행하며 각 단계 Motor-CAD GUI/출력 확인):
%   S0  경로/AF 수식 준비 + Emag 기준값 로드
%   S1  Motor-CAD 열기 (e10Turn6V261SLFEA_customLoss.mot, GUI 표시)
%   S2  [체크포인트] 원본 빌드 Lab 런타임 AC 손실 vs Emag Hybrid 스케일 확인
%       → verifyLabVsEmag_e10.m 발견사항: .mot 저장 테이블은 Emag Hybrid의 1/8
%         (48S/8P 대칭). Lab "런타임"이 풀머신인지 여기서 확정 → acScale 결정
%   S3  LabLink.txt 생성 (AC 컬럼 스케일 반영)
%   S4  Link='Custom (Advanced)' + LoadExternalModel_Lab → 동일 운전점 재확인
%   S5  baseline 효율맵 (Custom Loss 없음)
%   S6  AF Internal Custom Loss 등록 (+허용 변수 검증, read-back)
%   S7  [체크포인트] 운전점 Custom Loss vs 기대값 (AF(s)-1)·P_AC
%   S8  AF 효율맵
%   S9  결과 추출/비교 (Δη)
%
% [사전조건] Motor-CAD 실행 가능, eMach 루트 path (S0에서 추가)
% 관련: verifyLabVsEmag_e10.m (Phase 0), +mcad/buildAfCustomLossFormula.m,
%       +mcad/addLabInternalCustomLoss.m, +mcad/importExternalTxtLabModel.m

%% [S0] 경로/AF 수식 준비
scriptDir = fileparts(mfilename('fullpath'));
eMachRoot = fullfile(scriptDir, '..', '..');
addpath(genpath(eMachRoot));

MODEL        = 'SC';
AF_METHOD    = 'A';                 % 'A' 속도 다항식 | 'B' 3D RBF(길이 제한 리스크)
slfeaMot     = 'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot';          % LabLink 소스
workMot      = 'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_customLoss.mot'; % 작업 사본
labLinkDir   = 'D:\KangDH\Thesis\e10\SLFEA\LabLink';
afJsonPath   = fullfile(scriptDir, 'map_exports', 'e10', MODEL, ...
                        sprintf('AF_RBF_model_%s.json', MODEL));
% SLFEA.mot을 직접 스윕한 Emag 데이터 (체크포인트 기준값)
jsonSCPath   = fullfile(scriptDir, 'map_exports', 'e10', MODEL, ...
                        sprintf('JEET_ACLoss_%s_Map_Summary.json', MODEL));
outDir       = fullfile(scriptDir, 'map_exports', 'e10', MODEL, 'lab_af');
if ~isfolder(outDir), mkdir(outDir); end

% AF 수식 생성
[afFormula, afInfo] = mcad.buildAfCustomLossFormula(afJsonPath, AF_METHOD);
fprintf('=== AF 수식 (Method %s, %d자) ===\n%s\n', afInfo.method, afInfo.nChars, afFormula);
if strcmpi(AF_METHOD, 'A')
    afCoeffs = afInfo.coeffs;   % [a b c] — S7 기대값 계산용
    AFfun = @(s_krpm) polyval(afCoeffs, s_krpm);   % AF(s), s in kRPM
    fprintf('AF(2)=%.3f, AF(8)=%.3f, AF(16)=%.3f\n', AFfun(2), AFfun(8), AFfun(16));
end

% Emag Hybrid 기준값 (체크포인트용): 2000rpm / 460.05Arms / 36deg
% JEET_ACLoss_SC_Map_Summary.json = SLFEA.mot을 타 PC에서 직접 스윕한 데이터
scRaw = jsondecode(fileread(jsonSCPath));
rawSC = scRaw.records;
if ~iscell(rawSC), rawSC = num2cell(rawSC); end
chkSpeed = 2000; chkIrms = 460.05; chkPhase = 36.0;
P_hyb_ref = NaN; P_ts_ref = NaN;
for i = 1:numel(rawSC)
    p = rawSC{i};
    if abs(p.speed-chkSpeed)<1 && abs(p.current-chkIrms)<1 && abs(p.phase-chkPhase)<0.5
        if p.proximity_model == 1 && isfield(p, 'hybrid_total_kW')
            P_hyb_ref = p.hybrid_total_kW * 1000;
        elseif p.proximity_model == 3
            if isfield(p,'fea_per_turn_sum_kW') && isfield(p,'ts_dc_active_kW')
                P_ts_ref = (p.fea_per_turn_sum_kW - p.ts_dc_active_kW) * 1000;
            elseif isfield(p,'fea_total_ac_kW')
                P_ts_ref = p.fea_total_ac_kW * 1000;
            end
        end
    end
end
fprintf('\nEmag 기준(%drpm/%.1fArms/%.0fdeg): Hybrid=%.1f W, FullFEA=%.1f W\n', ...
    chkSpeed, chkIrms, chkPhase, P_hyb_ref, P_ts_ref);
assert(~isnan(P_hyb_ref), 'SC json에서 체크포인트 Hybrid 기준값을 못 찾음');
assert(isfile(workMot), '작업 .mot 없음: %s', workMot);

%% [S1] Motor-CAD 열기 (GUI 표시 유지 — 단계별 육안 확인용)
% --- v261 버전 가드: COM 등록이 어느 버전 exe를 가리키는지 사전 확인 ---
% .mot이 2026.1 포맷이므로 반드시 v261이 열려야 함 (다른 버전이면 포맷 변환 위험)
comExe = '';
try
    clsid  = winqueryreg('HKEY_CLASSES_ROOT', 'motorcad.appautomation\CLSID');
    try
        comExe = winqueryreg('HKEY_LOCAL_MACHINE', ...
            ['SOFTWARE\WOW6432Node\Classes\CLSID\' clsid '\LocalServer32']);
    catch
        comExe = winqueryreg('HKEY_LOCAL_MACHINE', ...
            ['SOFTWARE\Classes\CLSID\' clsid '\LocalServer32']);
    end
catch e
    warning('COM 등록 확인 실패(%s) — 실행 후 버전을 직접 확인할 것', e.message);
end
fprintf('[S1] COM 서버: %s\n', comExe);
motVer = mcad.getMotProgramVersion(workMot);
fprintf('[S1] .mot 버전: %s (%s)\n', motVer.raw, motVer.majorMinor);
if ~isempty(comExe) && ~contains(comExe, 'v261')
    error(['motorcad.appautomation COM 등록이 v261이 아님!\n  현재: %s\n' ...
           '  해결: Motor-CAD 2026R1을 한 번 실행(재등록)하거나 activex.bat 경로 확인'], comExe);
end

mcadApp = actxserver('motorcad.appautomation');
mcadApp.SetVariable('MessageDisplayState', 2);   % 팝업만 억제 (GUI는 표시)
mcadApp.LoadFromFile(workMot);
fprintf('로드 완료: %s\n', workMot);
[~, isBuilt] = mcadApp.GetModelBuilt_Lab();
fprintf('Lab 모델 빌드 상태: %d\n', double(isBuilt));

%% [S2] 체크포인트 A — 원본 빌드 Lab 런타임 스케일 확인
% Phase 0 발견 (verifyLabVsEmag_e10.m, SC json=SLFEA 직접 스윕 기준):
%   .mot 저장 Lab 테이블 AC = Emag Hybrid(SLFEA)의 1/16 (2k/4k에서 ×16 시 1.01)
%   (참고: SLFEA_Half 스윕 대비로는 1/8 — Half는 축장 절반 모델로 2배 관계)
% 여기서는 Lab "런타임"이 저장 테이블에 내부 배율 M을 곱하는지 확인:
%   runtime ≈ M × table × speedScale.  외부 txt도 동일 M으로 해석된다고 가정하면
%   txt 값 = 풀머신 Hybrid가 되도록 acScale = P_hyb / runtime = 1/ratioRt 로 결정
%   (가정 검증은 S4에서 임포트 후 동일 운전점 재계산으로 수행 — 불일치 시 S3 재실행)
mcadApp.SetMotorLABContext();
% 운전점 정의: 전류+위상 지정 모드. OpPointSpec_MotorLAB enum이 문서화돼 있지 않아
% 후보값을 순회하며 달성 운전점(read-back)이 요구값과 일치하는 spec을 자동 탐색
mcadApp.SetVariable('SpeedDemand_MotorLAB', chkSpeed);
mcadApp.SetVariable('StatorCurrentDemand_RMS_Lab', chkIrms);
mcadApp.SetVariable('PhaseAdvanceDemand_Lab', chkPhase);

specFound = false;
triedLog = {};
for spec = [1 2 0 3 4]
    try
        mcadApp.SetVariable('OpPointSpec_MotorLAB', spec);
        mcadApp.CalculateOperatingPoint_Lab();
    catch e
        triedLog{end+1} = sprintf('spec=%d: 계산 실패(%s)', spec, e.message); %#ok<SAGROW>
        continue
    end
    [~, opIrms]  = mcadApp.GetVariable('LabOpPoint_StatorCurrent_Phase_RMS');
    [~, opPhAdv] = mcadApp.GetVariable('LabOpPoint_PhaseAdvance');
    triedLog{end+1} = sprintf('spec=%d: Irms=%.1f, PhAdv=%.1f', ...
        spec, double(opIrms), double(opPhAdv)); %#ok<SAGROW>
    if abs(double(opIrms)-chkIrms) < 5 && abs(double(opPhAdv)-chkPhase) < 2
        specFound = true;
        opSpecUsed = spec;
        break
    end
end
if ~specFound
    error('요구 운전점(%.0fArms/%.0fdeg) 달성 spec 없음:\n  %s', ...
        chkIrms, chkPhase, strjoin(triedLog, newline));
end
[~, opPacAC] = mcadApp.GetVariable('LabOpPoint_StatorCopperLoss_AC');
[~, opPfe]   = mcadApp.GetVariable('LabOpPoint_IronLoss');
fprintf('\n[S2] OpPointSpec=%d 채택. 달성 운전점: Irms=%.1f A, PhAdv=%.1f deg (요구: %.1f/%.0f)\n', ...
    opSpecUsed, double(opIrms), double(opPhAdv), chkIrms, chkPhase);
ratioRt = double(opPacAC) / P_hyb_ref;
fprintf('[S2] Lab 런타임 AC=%.1f W vs Emag Hybrid=%.1f W → ratioRt=%.4f\n', ...
    double(opPacAC), P_hyb_ref, ratioRt);
fprintf('     IronLoss(런타임)=%.1f W (참고)\n', double(opPfe));

% txt AC 컬럼 배율: acScale = 1/ratioRt 를 {1, 2, 8, 16} 중 가까운 값으로 스냅
%   유도: runtime = M×table×f(speed), 측정 ratioRt = M/16.
%         txt도 M배로 해석된다고 가정 → 풀머신이 되려면 txt = table×(16/M) = table×(1/ratioRt)
%   ratioRt≈1    → acScale=1  (내부 배율 M=16이 이미 풀머신 환산 → txt는 저장값 그대로)
%   ratioRt≈1/16 → acScale=16 (내부 배율 없음 → txt에 풀머신 절대값 기입)
candidates = [1 2 8 16];
[~, iBest] = min(abs(log(candidates * ratioRt)));   % candidates*ratioRt가 1에 가까운 것
acScale = candidates(iBest);
fprintf('     → acScale = %g (후보 {1,2,8,16} 중 1/ratioRt=%.2f에 스냅)\n', acScale, 1/ratioRt);
if abs(acScale * ratioRt - 1) > 0.15
    warning('acScale×ratioRt=%.3f가 1에서 멂 — S4 재검증 결과로 수동 조정 필요', acScale*ratioRt);
end

%% [S3] LabLink.txt 생성 (SLFEA.mot → 테이블 → AC 스케일 → txt)
% getMCADLabDataFromMotFile(mot, txtDir) 내부 흐름을 스케일 반영 위해 수동 전개
T_lab = getMCADLabDataFromMotFile(slfeaMot);
fprintf('[S3] Lab 테이블: %d 운전점 × %d 변수\n', height(T_lab), width(T_lab));

assert(~isnan(acScale), 'S2에서 acScale 미확정 — 수동 설정 후 진행');
acCols = T_lab.Properties.VariableNames( ...
    contains(T_lab.Properties.VariableNames, 'AC Copper Loss') | ...
    strcmp(T_lab.Properties.VariableNames, 'Stator_Copper_Loss_AC'));
for c = acCols
    T_lab.(c{1}) = T_lab.(c{1}) * acScale;
end
fprintf('     AC 컬럼 %d개에 ×%g 적용\n', numel(acCols), acScale);

T_link = reNameLabTable2LabLink(T_lab);
if ~isfolder(labLinkDir), mkdir(labLinkDir); end
labLinkTxtPath = makeLabLinkTXTFromLabTable(T_link, labLinkDir);
% 파일명 명시적으로 변경 (덮어쓰기 방지 + 이력)
namedTxt = fullfile(labLinkDir, sprintf('e10SLFEA_LabLink_ac%gx.txt', acScale));
movefile(labLinkTxtPath, namedTxt, 'f');
labLinkTxtPath = namedTxt;
fprintf('     LabLink txt: %s\n', labLinkTxtPath);
fprintf('     >> txt를 열어 헤더/값 육안 확인 후 다음 셀 진행 <<\n');

%% [S4] Custom (Advanced) Link + 외부 모델 로드 → 동일 운전점 재검증
mcadApp.SetVariable('ACLossHighFrequencyScaling_Method', 0);   % MCADLabManager 흐름과 동일
mcadApp.SetVariable('CurrentSpec_MotorLAB', 0);                % peak 기준
mcadApp.SetVariable('MaxModelCurrent_MotorLAB', max(T_lab.SatModel_Is_Lab));
mcad.importExternalTxtLabModel(mcadApp, labLinkTxtPath);

% 동일 운전점 재계산 → 원본 빌드값과 비교 (txt 해석 스케일/단위 검증)
mcadApp.CalculateOperatingPoint_Lab();
[~, opPacAC2] = mcadApp.GetVariable('LabOpPoint_StatorCopperLoss_AC');
[~, opPfe2]   = mcadApp.GetVariable('LabOpPoint_IronLoss');
[~, opTrq2]   = mcadApp.GetVariable('LabOpPoint_ShaftTorque');
fprintf('\n[S4] External txt 로드 후 동일 운전점:\n');
fprintf('     AC: %.1f W (원본 빌드 %.1f W, Emag Hybrid %.1f W)\n', ...
    double(opPacAC2), double(opPacAC), P_hyb_ref);
fprintf('     IronLoss: %.1f W (원본 %.1f W), Torque: %.1f Nm\n', ...
    double(opPfe2), double(opPfe), double(opTrq2));

% 하드 가드: txt 해석 스케일 검증 실패 시 맵 계산으로 넘어가지 않음
ratioAfter = double(opPacAC2) / P_hyb_ref;
if abs(ratioAfter - 1) > 0.25
    error(['[S4] External txt 로드 후 AC(%.1f W)가 Emag Hybrid(%.1f W)와 불일치 ' ...
           '(ratio=%.3f).\ntxt 해석 스케일 가정이 틀림 → acScale=%g 재검토 ' ...
           '(런타임 배율 M 가정 오류 가능). S3의 acScale을 %.2g로 수동 설정 후 재실행.'], ...
        double(opPacAC2), P_hyb_ref, ratioAfter, acScale, acScale / ratioAfter);
end
if double(opPfe2) > 5 * max(double(opPfe), 1) || double(opPfe2) < 0.2 * double(opPfe)
    error(['[S4] 철손이 원본(%.1f W) 대비 %.1f W로 크게 벗어남 — LabLink txt 철손 컬럼 ' ...
           '단위(W 절대값 vs W/Hz 계수) 불일치 가능성. 진행 중단.'], ...
        double(opPfe), double(opPfe2));
end
fprintf('     ✓ AC 스케일/철손 검증 통과 (AC ratio=%.3f)\n', ratioAfter);
mcadApp.SaveToFile(workMot);

%% [S5] baseline 효율맵 (Custom Loss 없음)
mcadApp.SetMotorLABContext();
mcadApp.SetVariable('EmagneticCalcType_Lab', 1);      % 1 = Efficiency Map
mcadApp.SetVariable('SpeedMin_MotorLAB', 0);
mcadApp.SetVariable('SpeedMax_MotorLAB', 16000);
mcadApp.SetVariable('Speedinc_MotorLAB', 500);
mcadApp.SetVariable('CurrentSpec_MotorLAB', 1);       % RMS 입력
mcadApp.SetVariable('Imax_RMS_MotorLAB', 460);
mcadApp.SetVariable('Imin_MotorLAB', 0);
% 드라이브 설정(Vdc 등)은 .mot 저장값 유지 — 현재값 로그만
for v = {'DCBusVoltage', 'ControlStrat_MotorLAB', 'ModulationIndex_MotorLAB', 'OperatingMode_Lab'}
    [~, val] = mcadApp.GetVariable(v{1});
    fprintf('  %s = %s\n', v{1}, num2str(double(val)));
end
fprintf('[S5] baseline 효율맵 계산 시작 (수 분 소요) ...\n');
tic; mcadApp.CalculateMagnetic_Lab(); toc

[~, labResultDir] = mcadApp.GetVariable('ResultsPath_MotorLAB');
srcMat = fullfile(strtrim(char(labResultDir)), 'MotorLAB_elecdata.mat');
assert(isfile(srcMat), 'Lab 결과 mat 없음: %s', srcMat);
baselineMat = fullfile(outDir, 'MotorLAB_elecdata_baseline.mat');
copyfile(srcMat, baselineMat);
fprintf('[S5] baseline 저장: %s\n', baselineMat);

%% [S6] AF Internal Custom Loss 등록
% 허용 변수 검증
[~, availVars] = mcadApp.GetVariable('CustomLossVariablesInternal_Lab');
availVars = char(availVars);
fprintf('[S6] Custom Loss 허용 변수 목록:\n%s\n', availVars);
for rv = afInfo.requiredVars
    if ~contains(availVars, rv{1}, 'IgnoreCase', true)
        warning('수식 변수 "%s"가 허용 목록에 없음! GUI에서 변수명 확인 필요', rv{1});
    end
end

lossName = sprintf('AF_%s_%s', afInfo.method, MODEL);
[idx0, rb] = mcad.addLabInternalCustomLoss(mcadApp, lossName, afFormula, 'Electrical', -1);
fprintf('[S6] 등록 완료 (index %d): %s\n', idx0, rb.name);
fprintf('     >> GUI Lab > Calculation(Losses)에서 "%s" 항목/수식 육안 확인 <<\n', lossName);
mcadApp.SaveToFile(workMot);

%% [S7] 체크포인트 B — 운전점 Custom Loss vs 기대값
chkSpeed7 = 8000;   % AF 보간 영역 내 속도 (2k~16k)
mcadApp.SetVariable('SpeedDemand_MotorLAB', chkSpeed7);
mcadApp.SetVariable('StatorCurrentDemand_RMS_Lab', chkIrms);
mcadApp.SetVariable('PhaseAdvanceDemand_Lab', chkPhase);
mcadApp.CalculateOperatingPoint_Lab();

[~, opPacAC7] = mcadApp.GetVariable('LabOpPoint_StatorCopperLoss_AC');
[~, opCustom] = mcadApp.GetVariable('LabOpPoint_CustomLoss_Total_Internal');
ratioCustom = double(opCustom) / double(opPacAC7);
fprintf('\n[S7] %d rpm / %.0f Arms / %.0f deg:\n', chkSpeed7, chkIrms, chkPhase);
fprintf('     Stator_Copper_Loss_AC = %.1f W\n', double(opPacAC7));
fprintf('     CustomLoss_Total_Internal = %.1f W → 비율 %.4f\n', double(opCustom), ratioCustom);
if strcmpi(AF_METHOD, 'A')
    expected = AFfun(chkSpeed7/1000) - 1;
    fprintf('     기대값 AF(%.0fk)-1 = %.4f → %s\n', chkSpeed7/1000, expected, ...
        ternary(abs(ratioCustom-expected) < 0.02, 'OK ✓', '불일치'));
    if abs(ratioCustom - expected) >= 0.02
        error(['[S7] Custom Loss 비율(%.4f)이 기대값 AF(s)-1=%.4f과 불일치 — ' ...
               '수식 문법(** 연산자)/변수명/Speed 단위 문제. GUI Lab > Losses에서 ' ...
               '수식 파싱 상태 확인 필요. AF 효율맵 진행 중단.'], ratioCustom, expected);
    end
end

%% [S8] AF 효율맵
fprintf('[S8] AF 적용 효율맵 계산 시작 ...\n');
tic; mcadApp.CalculateMagnetic_Lab(); toc
afMat = fullfile(outDir, sprintf('MotorLAB_elecdata_AF_%s.mat', afInfo.method));
copyfile(srcMat, afMat);
fprintf('[S8] AF 맵 저장: %s\n', afMat);

%% [S9] 결과 추출/비교 (Δη contour)
B = load(baselineMat);
A = load(afMat);
Speed  = B.Speed;  Torque = B.Shaft_Torque;
EffB   = B.Efficiency;  EffA = A.Efficiency;
if max(EffB(:)) <= 1.5, EffB = EffB*100; EffA = EffA*100; end
dEff = EffA - EffB;

figure('Name', 'AF Custom Loss 효율맵 비교', 'Position', [80 80 1500 420]);
subplot(1,3,1);
contourf(Speed, Torque, EffB, 90:0.5:98); colorbar; title('baseline \eta [%]');
xlabel('Speed [rpm]'); ylabel('Torque [Nm]');
subplot(1,3,2);
contourf(Speed, Torque, EffA, 90:0.5:98); colorbar; title(sprintf('AF %s \\eta [%%]', afInfo.method));
xlabel('Speed [rpm]');
subplot(1,3,3);
contourf(Speed, Torque, dEff); colorbar; title('\Delta\eta = AF - baseline [%p]');
xlabel('Speed [rpm]');
saveas(gcf, fullfile(outDir, sprintf('effmap_compare_AF_%s.png', afInfo.method)));

fprintf('\n[S9] Δη 통계: min %.3f / median %.3f / max %.3f [%%p]\n', ...
    min(dEff(:)), median(dEff(:), 'omitnan'), max(dEff(:)));
fprintf('     산출물: %s\n', outDir);
fprintf('     * 고속·고전류 영역에서 Δη<0 (손실 증가) 방향인지 확인\n');

%% 로컬 함수
function out = ternary(cond, a, b)
    if cond, out = a; else, out = b; end
end
