%% verifyLabVsEmag_e10.m
% Phase 0 — Lab 모델 데이터 vs Emag 스윕 데이터 일치성 검증 (판정 게이트)
%
% 배경:
%   AF(Adjustment Factor)는 Emag 스윕(Hybrid vs FullFEA, do_magnetic_calculation)
%   기반으로 피팅됐는데, Motor-CAD Lab Custom Link에 넣을 LabLink.txt 소스는
%   Lab build 데이터임. 둘이 같은 값인지 미확인 상태라 이 스크립트로 검증한다.
%
% 비교 항목:
%   [2] AC 손실 (핵심): SLFEA Lab 테이블 Stator_Copper_Loss_AC (W @n2ac 기준속도)
%       vs JEET_ACLoss_SC_Map_Summary.json의 Emag Hybrid / FullFEA
%       (이 json은 e10Turn6V261SLFEA.mot 자체를 다른 PC에서 전류·위상·속도 스윕한
%        데이터 — SLFEA 모델과 직접 매칭되는 Emag 기준. 180Map은 SLFEA_Half 모델)
%       → Lab 값이 Hybrid/FullFEA 중 어느 쪽인지 판정 (AF 이중보정 여부 결정)
%   [3] 쇄교자속: SLFEA Lab PsiD/PsiQ vs e10_SatuMap.mat (refModel Lab 기반)
%   [4] 철손: SLFEA Lab FeLoss 성분합 (W @참조속도) vs e10_SatuMap Iron_Loss
%
% 판정 게이트 (runAFCustomLossLab.m 진행 방향 결정):
%   케이스 1: Lab AC ≈ Emag Hybrid  → Lab build 기반 LabLink.txt + AF 수식 그대로
%   케이스 2: 어느 쪽과도 불일치     → LabLink AC 컬럼을 Emag Hybrid 데이터로 치환
%   케이스 3: Lab AC ≈ FullFEA      → AF 적용 시 이중보정 → 목적 재확인 필요
%
% [사전조건] eMach 루트 path 등록 (Cell [0]), Motor-CAD 실행 불필요(.mot 파싱만)

%% [0] 경로 설정
scriptDir = fileparts(mfilename('fullpath'));          % .../mlxperPJT/JEET
eMachRoot = fullfile(scriptDir, '..', '..');           % .../eMach
addpath(genpath(eMachRoot));

slfeaMotPath = 'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot';
satuMapPath  = fullfile(eMachRoot, 'tools', 'SystemSimulationModel', 'e10_SatuMap.mat');
jsonSCPath   = fullfile(scriptDir, 'map_exports', 'e10', 'SC', ...
                        'JEET_ACLoss_SC_Map_Summary.json');   % SLFEA.mot 직접 스윕 데이터

zetaAC       = 2;      % Lab AC 손실 속도 스케일링 지수 (scaleSpeedCoilACLoss 기본값)
iMinValid    = 1.0;    % [A RMS] near-zero 전류 제외 임계값 (다른 물리 레짐)

assert(isfile(slfeaMotPath), '.mot 없음: %s', slfeaMotPath);
assert(isfile(satuMapPath),  'SatuMap 없음: %s', satuMapPath);
assert(isfile(jsonSCPath),   'SC Map JSON 없음: %s', jsonSCPath);

fprintf('SLFEA .mot : %s\n', slfeaMotPath);
fprintf('SatuMap    : %s (refModel Lab 기반 주의)\n', satuMapPath);
fprintf('SC Map     : %s\n             (Emag 스윕 — SLFEA.mot을 타 PC에서 직접 해석한 데이터)\n', jsonSCPath);

%% [1] SLFEA Lab 빌드 설정 리포트 + Lab 테이블 추출
% 빌드 설정은 .mot 텍스트에서 직접 읽음 (INI 형식 key=value)
motText = fileread(slfeaMotPath);

keys = {'CalcTypeCuLoss_MotorLAB', 'LabModel_ACLoss_Method', ...
        'LabModel_ACLoss_CalculationMethod', 'n2ac_MotorLAB', ...
        'AcLossFreq_MotorLAB', 'FEALossMap_RefSpeed_Lab', ...
        'ElectroLink_MotorLAB', ...
        'ModelBuildPoints_Current_Lab', 'ModelBuildPoints_Gamma_Lab'};

fprintf('\n=== [1] SLFEA Lab 빌드 설정 (.mot 직접 파싱) ===\n');
motSetting = struct();
for k = 1:numel(keys)
    tok = regexp(motText, ['^\s*' keys{k} '=([^\r\n]*)'], 'tokens', 'lineanchors');
    if isempty(tok)
        fprintf('  %-38s = (없음)\n', keys{k});
        continue
    end
    vals = cellfun(@(c) strtrim(c{1}), tok, 'UniformOutput', false);
    vals = unique(vals, 'stable');
    motSetting.(keys{k}) = vals;
    fprintf('  %-38s = %s\n', keys{k}, strjoin(vals, ' | '));
end
fprintf(['  * CalcTypeCuLoss_MotorLAB=3 / LabModel_ACLoss_Method=3 이면\n' ...
         '    Lab AC 손실이 FEA 기반 빌드일 가능성 → [2]에서 수치로 판정\n']);

n2ac_rpm = str2double(motSetting.n2ac_MotorLAB{1});          % AC 손실 기준속도
refSpeed_rpm = str2double(motSetting.FEALossMap_RefSpeed_Lab{1});  % 철손 기준속도

% Lab 맵 테이블 추출 (.mot 파싱, gen_e10_satumap_from_mot.m 과 동일 경로)
fprintf('\ngetMCADLabDataFromMotFile 실행 중 ...\n');
T = getMCADLabDataFromMotFile(slfeaMotPath);
fprintf('완료: %d 운전점 × %d 변수\n', height(T), width(T));

% 필수 컬럼 확인 (실측 컬럼명: gen_e10_satumap_from_mot.m 참조)
requiredCols = {'SatModel_Is_Lab', 'SatModel_Gamma_Lab', 'Id_Peak', 'Iq_Peak', ...
                'PsiDModel_Lab', 'PsiQModel_Lab', 'Stator_Copper_Loss_AC'};
missing = requiredCols(~ismember(requiredCols, T.Properties.VariableNames));
assert(isempty(missing), '테이블 컬럼 없음: %s\n(컬럼 목록: %s)', ...
    strjoin(missing, ', '), strjoin(T.Properties.VariableNames, ', '));

Is_pk_lab  = T.SatModel_Is_Lab;       % [A peak]
gamma_lab  = T.SatModel_Gamma_Lab;    % [deg]
Pac_lab_W  = T.Stator_Copper_Loss_AC; % [W @ n2ac_rpm]

fprintf('Lab 격자: Is %d점 [%.1f ~ %.1f Apk], Gamma %d점 [%.0f ~ %.0f deg]\n', ...
    numel(unique(Is_pk_lab)), min(Is_pk_lab), max(Is_pk_lab), ...
    numel(unique(gamma_lab)), min(gamma_lab), max(gamma_lab));
fprintf('Lab AC 손실 범위: %.3f ~ %.1f W @ %d rpm\n', ...
    min(Pac_lab_W), max(Pac_lab_W), n2ac_rpm);

%% [2] AC 손실 비교 (핵심): Lab vs Emag Hybrid vs FullFEA
% SC Map JSON({_meta, records}): proximity_model==1(Hybrid) / ==3(FullFEA)
% current는 RMS (_mcad_parallel_worker가 RMSCurrent로 설정). 스윕은 920 Arms까지
% 있으나 Lab 모델 범위(460 Arms=650.5 Apk)를 넘는 점은 보간 불가로 자동 제외됨.
scRaw = jsondecode(fileread(jsonSCPath));
raw   = scRaw.records;
if ~iscell(raw), raw = num2cell(raw); end   % 필드 이질성에 따라 cell/struct 배열 가변

getf = @(s, f, d) subsrefOrDefault(s, f, d);   % 로컬 함수 (하단 정의)

nPts = numel(raw);
spd  = nan(nPts,1); cur = nan(nPts,1); phs = nan(nPts,1);
prox = nan(nPts,1); Phyb = nan(nPts,1); Pts_ = nan(nPts,1);
for i = 1:nPts
    p = raw{i};
    spd(i)  = p.speed;  cur(i) = p.current;  phs(i) = p.phase;
    prox(i) = p.proximity_model;
    if prox(i) == 1
        Phyb(i) = getf(p, 'hybrid_total_kW', NaN) * 1000;
    else
        % FullFEA AC 활성부: 우선순위 ts_ac_active_only → per_turn_sum - dc_active
        v = getf(p, 'ts_ac_active_only_kW', NaN);
        if isnan(v) || v <= 0
            pSum = getf(p, 'fea_per_turn_sum_kW', NaN);
            pDc  = getf(p, 'ts_dc_active_kW', getf(p, 'ts_dc_active_only_kW', NaN));
            if ~isnan(pSum) && ~isnan(pDc)
                v = pSum - pDc;
            else
                v = getf(p, 'fea_total_ac_kW', NaN);   % 최후 fallback
            end
        end
        Pts_(i) = v * 1000;
    end
end

% Hybrid/FullFEA 포인트를 (speed,current,phase)로 매칭
hybIdx = find(prox == 1);
nH = numel(hybIdx);
mSpd = nan(nH,1); mCur = nan(nH,1); mPhs = nan(nH,1);
mHyb = nan(nH,1); mTS  = nan(nH,1);
for ii = 1:nH
    i = hybIdx(ii);
    j = find(prox == 3 & spd == spd(i) & ...
             abs(cur - cur(i)) < 1e-6 & abs(phs - phs(i)) < 1e-6, 1);
    if isempty(j), continue, end
    mSpd(ii) = spd(i);  mCur(ii) = cur(i);  mPhs(ii) = phs(i);
    mHyb(ii) = Phyb(i); mTS(ii)  = Pts_(j);
end
ok  = ~isnan(mHyb) & ~isnan(mTS);
cmp = table(mSpd(ok), mCur(ok), mPhs(ok), mHyb(ok), mTS(ok), ...
    'VariableNames', {'speed','Irms','phase','P_hyb_W','P_ts_W'});
fprintf('\n=== [2] AC 손실 비교: 매칭된 Emag 포인트 %d개 ===\n', height(cmp));

% Lab 보간자 (Is_pk, gamma 산점) → Emag 포인트 위치에서 평가
F_lab = scatteredInterpolant(Is_pk_lab, gamma_lab, Pac_lab_W, 'natural', 'none');
Is_pk_emag = cmp.Irms * sqrt(2);                 % RMS → peak
% 경계 수치오차 클램프 (460.05 Arms*√2 = 650.6 vs Lab 최대 650.5 Apk)
IsMaxLab = max(Is_pk_lab);
onEdge = Is_pk_emag > IsMaxLab & Is_pk_emag < IsMaxLab * 1.005;
Is_pk_emag(onEdge) = IsMaxLab;
P_lab_ref  = F_lab(Is_pk_emag, cmp.phase);       % W @ n2ac
cmp.P_lab_W = P_lab_ref .* (cmp.speed / n2ac_rpm).^zetaAC;   % 속도 스케일링

cmp.r_LabHyb = cmp.P_lab_W ./ cmp.P_hyb_W;
cmp.r_LabTS  = cmp.P_lab_W ./ cmp.P_ts_W;
cmp.AF_emag  = cmp.P_ts_W  ./ cmp.P_hyb_W;       % 참고: Emag 기준 AF

valid = cmp.Irms >= iMinValid & ~isnan(cmp.P_lab_W);
fprintf('통계 대상: %d/%d 포인트 (near-zero %.1fA 미만 및 보간범위 밖 제외)\n', ...
    nnz(valid), height(cmp), iMinValid);

speeds = unique(cmp.speed)';
fprintf('\n%8s | %12s | %12s | %12s\n', 'speed', 'Lab/Hybrid', 'Lab/FullFEA', 'AF(TS/Hyb)');
fprintf('%s\n', repmat('-', 1, 56));
for s = speeds
    m = valid & cmp.speed == s;
    fprintf('%6d | median %5.2f | median %5.2f | median %5.2f\n', ...
        s, median(cmp.r_LabHyb(m)), median(cmp.r_LabTS(m)), median(cmp.AF_emag(m)));
end
medHyb = median(cmp.r_LabHyb(valid));
medTS  = median(cmp.r_LabTS(valid));
fprintf('%s\n', repmat('-', 1, 56));
fprintf('%6s | median %5.2f | median %5.2f |\n', 'ALL', medHyb, medTS);

% --- 진단 1: 상수 배율 가설 (모델 대칭계수 등) ---
% Lab/Hyb가 속도·전류 무관하게 일정하면 순수 상수 배율 차이 → 배율 추정
kFit = median(cmp.P_hyb_W(valid) ./ cmp.P_lab_W(valid));
r8   = cmp.r_LabHyb(valid) * 8;    % 48S/8P 대칭(1/8 모델) 가설
fprintf('\n[진단1] Hybrid/Lab 상수배율 추정: k = %.2f\n', kFit);
fprintf('        1/8 대칭 가설(×8) 적용 시 Lab*8/Hybrid: median %.3f (IQR %.3f~%.3f)\n', ...
    median(r8), quantile(r8, 0.25), quantile(r8, 0.75));
fprintf('        Lab/Hyb 변동성: IQR %.3f ~ %.3f (일정하면 상수배율 가설 지지)\n', ...
    quantile(cmp.r_LabHyb(valid), 0.25), quantile(cmp.r_LabHyb(valid), 0.75));

% --- 진단 2: 최대전류(460A) 포인트 상세 ---
fprintf('\n[진단2] 460A 포인트 상세 (W):\n');
fprintf('%6s %6s | %10s %10s %10s | %7s\n', 'rpm', 'phase', 'Lab', 'Hybrid', 'FullFEA', 'Lab*8/H');
d2 = cmp(abs(cmp.Irms - 460) < 1 & valid, :);
for i = 1:height(d2)
    fprintf('%6d %6.0f | %10.1f %10.1f %10.1f | %7.3f\n', ...
        d2.speed(i), d2.phase(i), d2.P_lab_W(i), d2.P_hyb_W(i), d2.P_ts_W(i), ...
        8 * d2.P_lab_W(i) / d2.P_hyb_W(i));
end

% --- 진단 3: AC Copper Loss 컬럼(도체별) 개수 확인 ---
acCols = T.Properties.VariableNames(contains(T.Properties.VariableNames, 'AC Copper Loss'));
fprintf('\n[진단3] Lab 테이블 AC Copper Loss 컬럼 %d개: %s\n', ...
    numel(acCols), strjoin(acCols, ', '));

figure('Name', 'AC Loss: Lab vs Emag');
subplot(1,2,1);
scatter(cmp.P_hyb_W(valid), cmp.P_lab_W(valid), 30, cmp.speed(valid), 'filled');
hold on; grid on; axis equal
lim = [0, max([cmp.P_hyb_W(valid); cmp.P_lab_W(valid)])];
plot(lim, lim, 'k--'); xlim(lim); ylim(lim);
xlabel('Emag Hybrid [W]'); ylabel('Lab (\zeta=2 scaled) [W]');
title('Lab vs Hybrid'); colorbar; colormap(jet);
subplot(1,2,2);
scatter(cmp.P_ts_W(valid), cmp.P_lab_W(valid), 30, cmp.speed(valid), 'filled');
hold on; grid on; axis equal
lim = [0, max([cmp.P_ts_W(valid); cmp.P_lab_W(valid)])];
plot(lim, lim, 'k--'); xlim(lim); ylim(lim);
xlabel('Emag FullFEA (AC active only) [W]'); ylabel('Lab (\zeta=2 scaled) [W]');
title('Lab vs FullFEA'); colorbar;

%% [3] 쇄교자속 비교: SLFEA Lab vs e10_SatuMap (refModel Lab 기반)
% 주의: SatuMap도 Lab 데이터이므로 이는 SLFEA vs refModel 모델 간 일치성 확인임
S = load(satuMapPath);

F_psid = scatteredInterpolant(T.Id_Peak, T.Iq_Peak, T.PsiDModel_Lab, 'natural', 'none');
F_psiq = scatteredInterpolant(T.Id_Peak, T.Iq_Peak, T.PsiQModel_Lab, 'natural', 'none');

PsiD_at = F_psid(S.Id_Peak, S.Iq_Peak);
PsiQ_at = F_psiq(S.Id_Peak, S.Iq_Peak);
inHull  = ~isnan(PsiD_at);

errD = abs(PsiD_at - S.Flux_Linkage_D) ./ max(abs(S.Flux_Linkage_D), 1e-4);
errQ = abs(PsiQ_at - S.Flux_Linkage_Q) ./ max(abs(S.Flux_Linkage_Q), 1e-4);

fprintf('\n=== [3] 쇄교자속: SLFEA Lab vs SatuMap(refModel Lab) ===\n');
fprintf('비교 격자점: %d/%d (SLFEA 보간범위 내)\n', nnz(inHull), numel(inHull));
fprintf('PsiD 상대오차: median %.2f%%, max %.2f%%\n', ...
    100*median(errD(inHull)), 100*max(errD(inHull)));
fprintf('PsiQ 상대오차: median %.2f%%, max %.2f%%\n', ...
    100*median(errQ(inHull)), 100*max(errQ(inHull)));

% --- 진단 4: 범위·무부하 PM 플럭스 직접 비교 (스케일/단위 차이 판별) ---
zeroI = Is_pk_lab < 0.01;
fprintf('\n[진단4] PsiD 범위: SLFEA [%.4g, %.4g] Vs vs SatuMap [%.4g, %.4g] Vs\n', ...
    min(T.PsiDModel_Lab), max(T.PsiDModel_Lab), ...
    min(S.Flux_Linkage_D(:)), max(S.Flux_Linkage_D(:)));
fprintf('        PsiQ 범위: SLFEA [%.4g, %.4g] Vs vs SatuMap [%.4g, %.4g] Vs\n', ...
    min(T.PsiQModel_Lab), max(T.PsiQModel_Lab), ...
    min(S.Flux_Linkage_Q(:)), max(S.Flux_Linkage_Q(:)));
if any(zeroI)
    fprintf('        무부하 PM 플럭스: SLFEA %.5g Vs vs SatuMap(0,0 근방) %.5g Vs → 비율 %.3f\n', ...
        mean(T.PsiDModel_Lab(zeroI)), S.Flux_Linkage_D(end, 1), ...
        mean(T.PsiDModel_Lab(zeroI)) / max(S.Flux_Linkage_D(end, 1), 1e-9));
end
% SatuMap 격자 규약: 행=Id(-Imax→0), 열=Iq(0→Imax) → (end,1) = (Id=0, Iq=0)

%% [4] 철손 비교: SLFEA Lab 성분합 vs e10_SatuMap Iron_Loss
% 두 모델 모두 FEALossMap_RefSpeed_Lab 기준 절대 W 저장 (SLFEA=refModel=동일 참조속도 확인됨)
ironCols = {'FeLossBackIronHy_MotorLAB', 'FeLossToothHy_MotorLAB', ...
            'FeLossBackIronEd_MotorLAB', 'FeLossToothEd_MotorLAB', ...
            'FeLossRotorHy_MotorLAB',    'FeLossRotorPoleHy_MotorLAB', ...
            'FeLossRotorEd_MotorLAB',    'FeLossRotorPoleEd_MotorLAB'};
haveIron = ismember(ironCols, T.Properties.VariableNames);
fprintf('\n=== [4] 철손: SLFEA Lab vs SatuMap(refModel Lab) @ %d rpm ===\n', refSpeed_rpm);
if all(haveIron)
    Pfe_lab = sum(T{:, ironCols}, 2);
    F_fe = scatteredInterpolant(T.Id_Peak, T.Iq_Peak, Pfe_lab, 'natural', 'none');
    Fe_at = F_fe(S.Id_Peak, S.Iq_Peak);
    okFe  = ~isnan(Fe_at) & S.Iron_Loss > 1;   % 1W 미만 저손실점 제외
    errFe = abs(Fe_at(okFe) - S.Iron_Loss(okFe)) ./ S.Iron_Loss(okFe);
    fprintf('비교 격자점: %d, 상대오차: median %.2f%%, max %.2f%%\n', ...
        nnz(okFe), 100*median(errFe), 100*max(errFe));
else
    fprintf('철손 컬럼 부재: %s → 철손 비교 생략\n', ...
        strjoin(ironCols(~haveIron), ', '));
end

%% [5] 판정 게이트 요약
fprintf('\n================ 판정 게이트 ================\n');
fprintf('Lab/Hybrid  median = %.3f\n', medHyb);
fprintf('Lab/FullFEA median = %.3f\n', medTS);
dHyb = abs(medHyb - 1);  dTS = abs(medTS - 1);
if dHyb < 0.10 && dHyb < dTS
    fprintf(['→ 케이스 1: Lab AC ≈ Emag Hybrid (오차 %.1f%%)\n' ...
             '  Lab build 기반 LabLink.txt 사용 + AF 수식 그대로 적용 가능\n'], 100*dHyb);
elseif dTS < 0.10 && dTS < dHyb
    fprintf(['→ 케이스 3: Lab AC ≈ FullFEA (오차 %.1f%%)\n' ...
             '  AF Custom Loss 적용 시 이중보정! 목적 재확인 필요\n'], 100*dTS);
else
    fprintf(['→ 케이스 2: 어느 쪽과도 불일치 (Hyb %.1f%%, TS %.1f%%)\n' ...
             '  LabLink.txt의 AC Copper Loss 컬럼을 Emag Hybrid 데이터로 치환 권장\n'], ...
        100*dHyb, 100*dTS);
end
fprintf('=============================================\n');
fprintf('* 속도별 경향(위 [2] 표)과 산점도를 함께 보고 최종 판정할 것\n');
fprintf('* zetaAC=%g 가정이 어긋나면 속도별 ratio가 계통적으로 벌어짐 → 표에서 확인\n', zetaAC);

%% 로컬 함수
function v = subsrefOrDefault(s, f, d)
    if isfield(s, f), v = s.(f); else, v = d; end
end
