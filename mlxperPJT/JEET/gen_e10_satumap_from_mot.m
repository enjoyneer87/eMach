%% gen_e10_satumap_from_mot.m
% e10Turn6V261.mot → tools/SystemSimulationModel/e10_SatuMap.mat 변환 스크립트
%
% Motor-CAD ActiveX 없이 .mot 파일 파싱만으로 동작.
% getMCADLabDataFromMotFile 로 Lab 맵 데이터를 추출한 뒤
% Is-Gamma 산점을 정규 Id-Iq ndgrid 로 재보간하여 SatuMap 포맷으로 저장.
%
% 저장 필드 (기존 SatuMap 포맷과 동일한 이름):
%   Id_Peak, Iq_Peak                  (nId × nIq)
%   Flux_Linkage_D, Flux_Linkage_Q    (nId × nIq)
%   Iron_Loss                         (nId × nIq, W @참조속도)
%   Stator_Copper_Loss_AC             (nId × nIq, W @참조속도)
%   Phase_Resistance_DC_at_20C        (스칼라, Ω)
%
% 주의: tools/SystemSimulationModel/SatuMap.mat 은 Tesla Plaid 데이터.
%       반드시 e10_SatuMap.mat 에 저장(덮어쓰기 금지).

%% [0] 경로 설정
scriptDir = fileparts(mfilename('fullpath'));
eMachRoot = fullfile(scriptDir, '..', '..');
addpath(genpath(eMachRoot));

motPath = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot';
outPath = fullfile(eMachRoot, 'tools', 'SystemSimulationModel', 'e10_SatuMap.mat');

if ~isfile(motPath)
    error('[오류] .mot 파일 없음:\n  %s', motPath);
end
fprintf('[0] 입력: %s\n    출력: %s\n', motPath, outPath);

%% [1] .mot → Lab 맵 테이블 추출
fprintf('\n[1] getMCADLabDataFromMotFile 실행 중 ...\n');
T = getMCADLabDataFromMotFile(motPath);
fprintf('    완료: %d 운전점 × %d 변수\n', height(T), width(T));

varNames = T.Properties.VariableNames;
varUnits = T.Properties.VariableUnits;
fprintf('\n--- 컬럼 목록 (이름 | 단위) ---\n');
for k = 1:width(T)
    fprintf('  %-44s [%s]\n', varNames{k}, varUnits{k});
end

%% [2] 격자 구조 파악
Is_flat    = T.SatModel_Is_Lab;
Gamma_flat = T.SatModel_Gamma_Lab;
Is_uniq    = unique(Is_flat);
Gam_uniq   = unique(Gamma_flat);
nIs        = numel(Is_uniq);
nGamma     = numel(Gam_uniq);
Is_max     = max(Is_uniq);

fprintf('\n[2] Is-Gamma 격자\n');
fprintf('    Is:    %d 점  [%.1f ~ %.1f A]\n', nIs, min(Is_uniq), Is_max);
fprintf('    Gamma: %d 점  [%.1f ~ %.1f deg]\n', nGamma, min(Gam_uniq), max(Gam_uniq));
fprintf('    총 운전점: %d\n', height(T));

%% [3] 플럭스 링키지 컬럼 (getMCADLabDataFromMotFile 실측 컬럼명 하드코딩)
% 자동 정규식 탐지는 'PsiDModel_Lab' 같은 실제 이름(밑줄 없는 D/Q)에서 실패하므로
% 직접 지정한다. 컬럼명이 바뀌면 위 컬럼 목록 출력을 보고 갱신할 것.
FluxD_col = 'PsiDModel_Lab';
FluxQ_col = 'PsiQModel_Lab';

assert(ismember(FluxD_col, varNames), '>>> 컬럼 없음: %s (위 컬럼 목록 확인)', FluxD_col);
assert(ismember(FluxQ_col, varNames), '>>> 컬럼 없음: %s (위 컬럼 목록 확인)', FluxQ_col);

fprintf('\n[3] 플럭스 링키지 컬럼\n    D: %s\n    Q: %s\n', FluxD_col, FluxQ_col);

%% [4] 철손 계산: Lab FEA 손실맵 성분 직접 합산 (이미 참조속도 기준 절대 Watts)
% 모든 스케일러 파라미터는 getMcadActiveXTableFromMotFile 로 직접 읽음
ActiveXStr = mcad.getMcadActiveXTableFromMotFile(motPath);

refTbl = findAutomationNameFromAllCategory(ActiveXStr, 'FEALossMap_RefSpeed_Lab');
if ~isempty(refTbl)
    refSpeed_rpm = convertCharTypeData2ArrayData(refTbl.CurrentValue{1});
else
    refSpeed_rpm = 1000;
    warning('FEALossMap_RefSpeed_Lab 없음 → 기본값 %d RPM 사용', refSpeed_rpm);
end

fprintf('\n[4] 철손 계산\n    참조속도=%.0f rpm (Lab FEA 손실맵 빌드 속도)\n', refSpeed_rpm);

% getMCADLabDataFromMotFile 실측 컬럼명 (단위 Watts, 참조속도에서 이미 계산된 절대값).
% fromMCAD_lab_json.m의 Pfes_h/Pfes_c/Pfer_h/Pfer_c 분해와 동일한 합산 규약을 사용:
%   고정자(Pfes) = BackIron + Tooth,  회전자(Pfer) = Rotor + RotorPole,  각각 히스테리시스+에디
IronLossCols = {'FeLossBackIronHy_MotorLAB', 'FeLossToothHy_MotorLAB', ...   % Pfes_h
                'FeLossBackIronEd_MotorLAB', 'FeLossToothEd_MotorLAB', ...   % Pfes_c
                'FeLossRotorHy_MotorLAB',    'FeLossRotorPoleHy_MotorLAB', ... % Pfer_h
                'FeLossRotorEd_MotorLAB',    'FeLossRotorPoleEd_MotorLAB'};   % Pfer_c

missingIronCols = IronLossCols(~ismember(IronLossCols, varNames));
assert(isempty(missingIronCols), ...
    '>>> 철손 컬럼 없음: %s (위 컬럼 목록 확인)', strjoin(missingIronCols, ', '));

Iron_Loss_flat = zeros(height(T), 1);
for i = 1:numel(IronLossCols)
    Iron_Loss_flat = Iron_Loss_flat + T.(IronLossCols{i});
    fprintf('    + %-30s [Watts]\n', IronLossCols{i});
end
fprintf('    철손 범위: %.2f ~ %.2f W\n', min(Iron_Loss_flat), max(Iron_Loss_flat));

%% [5] DC 저항 (20°C 기준 온도 보정)
resTbl   = findAutomationNameFromAllCategory(ActiveXStr, 'Resistance_MotorLAB');
twdgTbl  = findAutomationNameFromAllCategory(ActiveXStr, 'Twdg_MotorLAB');
alphaTbl = findAutomationNameFromAllCategory(ActiveXStr, 'WindingAlpha_MotorLAB');

if ~isempty(resTbl) && ~isempty(twdgTbl) && ~isempty(alphaTbl)
    R_T   = convertCharTypeData2ArrayData(resTbl.CurrentValue{1});
    T_wdg = convertCharTypeData2ArrayData(twdgTbl.CurrentValue{1});
    alpha = convertCharTypeData2ArrayData(alphaTbl.CurrentValue{1});
    R_DC_20C = R_T / (1 + alpha * (T_wdg - 20));
    fprintf('\n[5] DC 저항\n    R(%.0f°C)=%.6f Ω, α=%.5f → R(20°C)=%.6f Ω\n', ...
        T_wdg, R_T, alpha, R_DC_20C);
elseif ~isempty(resTbl)
    R_DC_20C = convertCharTypeData2ArrayData(resTbl.CurrentValue{1});
    warning('온도 보정 파라미터 없음 → 모델 온도의 저항값 직접 사용: %.6f Ω', R_DC_20C);
else
    error('[오류] Resistance_MotorLAB 를 찾을 수 없음. 직접 지정 필요.');
end
Phase_Resistance_DC_at_20C = R_DC_20C;

%% [6] Is-Gamma 산점 → 정규 Id-Iq ndgrid 재보간
Id_flat = T.Id_Peak;
Iq_flat = T.Iq_Peak;

if ismember('Stator_Copper_Loss_AC', T.Properties.VariableNames)
    AcLoss_flat = T.Stator_Copper_Loss_AC;
else
    warning('Stator_Copper_Loss_AC 없음 → 0 으로 설정');
    AcLoss_flat = zeros(height(T), 1);
end

% Is~0 점들은 모두 (0,0)으로 수렴 → 대표값 1개로 통합
zeroMask = Is_flat < 0.01;

Id_scat = Id_flat(~zeroMask);
Iq_scat = Iq_flat(~zeroMask);
LD_scat = T.(FluxD_col)(~zeroMask);
LQ_scat = T.(FluxQ_col)(~zeroMask);
Fe_scat = Iron_Loss_flat(~zeroMask);
Ac_scat = AcLoss_flat(~zeroMask);

if any(zeroMask)
    LD0 = mean(T.(FluxD_col)(zeroMask));   % 무부하 d축 플럭스 (PM 플럭스)
    LQ0 = mean(T.(FluxQ_col)(zeroMask));   % ~0 for IPM
    Fe0 = mean(Iron_Loss_flat(zeroMask));   % 무부하 철손
else
    LD0 = 0;  LQ0 = 0;  Fe0 = 0;
end

Id_scat = [0;   Id_scat];
Iq_scat = [0;   Iq_scat];
LD_scat = [LD0; LD_scat];
LQ_scat = [LQ0; LQ_scat];
Fe_scat = [Fe0; Fe_scat];
Ac_scat = [0;   Ac_scat];   % Is=0 이면 AC 구리손 = 0

% 목표 직교 격자 (ndgrid 규약: 행=Id, 열=Iq)
% Id_Peak(:,1) → unique Id vector, Iq_Peak(1,:) → unique Iq vector
Id_vec = linspace(-Is_max, 0,      nIs)';
Iq_vec = linspace(0,       Is_max, nGamma);
[Id_Peak, Iq_Peak] = ndgrid(Id_vec, Iq_vec);

fprintf('\n[6] 재보간: 산점 %d 점 → ndgrid (%d × %d)\n', numel(Id_scat), nIs, nGamma);

F_ld = scatteredInterpolant(Id_scat, Iq_scat, LD_scat, 'natural', 'linear');
F_lq = scatteredInterpolant(Id_scat, Iq_scat, LQ_scat, 'natural', 'linear');
F_fe = scatteredInterpolant(Id_scat, Iq_scat, Fe_scat, 'natural', 'linear');
F_ac = scatteredInterpolant(Id_scat, Iq_scat, Ac_scat, 'natural', 'linear');

Flux_Linkage_D        = F_ld(Id_Peak, Iq_Peak);
Flux_Linkage_Q        = F_lq(Id_Peak, Iq_Peak);
Iron_Loss             = max(0, F_fe(Id_Peak, Iq_Peak));
Stator_Copper_Loss_AC = max(0, F_ac(Id_Peak, Iq_Peak));

%% [7] 저장 및 검증
% scipy.io.loadmat은 v7.3(HDF5)을 못 읽으므로 v7로 명시 저장
% (이 MATLAB 설치는 기본 저장 포맷 설정이 v7.3으로 되어 있어 플래그 생략 시 v7.3으로 저장됨)
save(outPath, ...
    'Id_Peak', 'Iq_Peak', ...
    'Flux_Linkage_D', 'Flux_Linkage_Q', ...
    'Phase_Resistance_DC_at_20C', ...
    'Iron_Loss', 'Stator_Copper_Loss_AC', ...
    '-v7');

fprintf('\n[7] 저장 완료: %s\n', outPath);

fprintf('\n=== 저장 내용 검증 ===\n');
S = load(outPath);
fn = fieldnames(S);
for i = 1:numel(fn)
    v = S.(fn{i});
    if isscalar(v)
        fprintf('  %-35s = %.6g\n', fn{i}, v);
    else
        fprintf('  %-35s  size=%-12s  range=[%.4g, %.4g]\n', ...
            fn{i}, mat2str(size(v)), min(v(:)), max(v(:)));
    end
end

fprintf('\n완료!\n');
