% test_phase1_verify.m
% -------------------------------------------------------------------------
% JEET 논문 Phase 1: Ref 효율맵 검증 — 단계별 점검 스크립트
%
% SyRE MMM 파이프라인(Motor-CAD Ref 모델 → 효율맵)을 단계별로 실행하며
% 각 단계의 PASS/FAIL 을 출력합니다. 전체 효율맵 검증(test_syre_efficiency_map.m)
% 을 돌리기 전에, 환경/데이터/오버라이드가 올바른지 빠르게 진단하는 용도입니다.
%
% 사용법: MATLAB 커맨드창에서 그냥 실행하면 됩니다.
%   >> test_phase1_verify
% -------------------------------------------------------------------------

clc; clear; close all;

%% 0. 경로 및 입력 파일 설정
current_dir = fileparts(mfilename('fullpath'));
emach_root  = fileparts(fileparts(current_dir));

% [중요] syre_public 을 먼저, eMach 를 나중에 addpath → eMach 오버라이드 우선
%        (addpath 는 prepend 이므로 나중에 추가한 폴더가 우선순위 높음)
syre_pub_root = 'D:\KangDH\gitSyREpub\syre_public';
addpath(genpath(syre_pub_root));   % 먼저 (낮은 우선순위)
addpath(genpath(emach_root));      % 나중에 (오버라이드 우선)

matPath = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261_SyreMMM_B.mat';
motPath = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot';

% 결과 집계용 카운터
nPass = 0; nFail = 0;

fprintf('\n');
fprintf('#########################################################\n');
fprintf('#  JEET Phase 1 검증 — 단계별 진단 (test_phase1_verify) #\n');
fprintf('#########################################################\n');

% 로컬 PASS/FAIL 헬퍼 (스크립트 하단 함수 정의 참조)
report = @(name, ok, msg) localReport(name, ok, msg);


%% STEP 1. 환경 확인 — eMach 오버라이드가 syre_public 보다 우선 잡히는가?
fprintf('\n========== STEP 1: 환경/오버라이드 우선순위 확인 ==========\n');
step1_ok = true;
checkFns = {'calcTnPoint', 'calcSkinEffect'};
for i = 1:numel(checkFns)
    fn   = checkFns{i};
    fpath = which(fn);
    fprintf('  which %-16s → %s\n', fn, fpath);
    if isempty(fpath)
        fprintf('    [경고] %s 를 path 에서 찾을 수 없습니다.\n', fn);
        step1_ok = false;
        continue;
    end
    % eMach\tools\syre 경로에서 잡혀야 정상 (syre_public 이면 오버라이드 실패)
    inEmach = contains(lower(fpath), lower(fullfile(emach_root, 'tools', 'syre')));
    inSyrePub = contains(lower(fpath), lower(syre_pub_root));
    if inEmach
        fprintf('    → eMach 오버라이드 적용됨 (OK)\n');
    elseif inSyrePub
        fprintf('    → [실패] syre_public 원본이 잡힘. addpath 순서 확인 필요!\n');
        step1_ok = false;
    else
        fprintf('    → [경고] 예상 외 경로. 수동 확인 필요.\n');
        step1_ok = false;
    end
end
[nPass, nFail] = bumpCounters(nPass, nFail, ...
    report('STEP 1 (오버라이드 우선순위)', step1_ok, ...
            'eMach tools/syre 가 syre_public 보다 우선'));


%% STEP 2. MAT 파일 필드 확인 — AC 손실 데이터 유무
fprintf('\n========== STEP 2: MAT 파일 AC손실 필드 확인 ==========\n');
fprintf('  파일: %s\n', matPath);
step2_ok = true;
hasAcLoss = false;
if ~exist(matPath, 'file')
    fprintf('  [실패] MAT 파일이 존재하지 않습니다.\n');
    step2_ok = false;
else
    S = load(matPath);
    if ~isfield(S, 'FluxMap_dq')
        fprintf('  [실패] FluxMap_dq 구조체가 MAT 파일에 없습니다.\n');
        step2_ok = false;
    else
        fm = S.FluxMap_dq;
        needFields = {'Pac_total_kW', 'speed_vec'};
        for i = 1:numel(needFields)
            f = needFields{i};
            present = isfield(fm, f);
            fprintf('  FluxMap_dq.%-14s : %s\n', f, ternary(present, '있음 (O)', '없음 (X)'));
        end
        hasAcLoss = isfield(fm, 'Pac_total_kW') && isfield(fm, 'speed_vec');
        if hasAcLoss
            fprintf('  → AC손실 데이터 존재: acLossFactor 자동 빌드 + SkinEffectFlag=Yes 예상\n');
            if isfield(fm, 'speed_vec')
                fprintf('     speed_vec: %d 포인트, 범위 %.0f – %.0f rpm\n', ...
                    numel(fm.speed_vec), min(fm.speed_vec), max(fm.speed_vec));
            end
        else
            fprintf('  → AC손실 데이터 없음: AC손실 없이 진행 (SkinEffectFlag=No)\n');
        end
        % 추가 비-2D 필드 존재 여부 (참고용)
        extraFields = {'Pac_prox_kW', 'Pac_skin_kW'};
        for i = 1:numel(extraFields)
            if isfield(fm, extraFields{i})
                fprintf('     (참고) %s 필드도 존재\n', extraFields{i});
            end
        end
    end
end
% STEP 2 는 "확인" 단계이므로 파일/구조체가 읽히면 PASS (AC손실 유무 자체는 정보)
[nPass, nFail] = bumpCounters(nPass, nFail, ...
    report('STEP 2 (MAT 필드 확인)', step2_ok, ...
            sprintf('AC손실 데이터 %s', ternary(hasAcLoss, '있음', '없음'))));


%% ───────────────────────────────────────────────────────────────────────
%% STEP 3. buildMotorModelForSyre 단독 실행 — 파라미터 추출 확인
%% ───────────────────────────────────────────────────────────────────────
fprintf('\n========== STEP 3: buildMotorModelForSyre 실행 ==========\n');
step3_ok = true;
motorModel = [];
try
    if exist(motPath, 'file')
        fprintf('  MOT 파일에서 파라미터 자동 추출 시도: %s\n', motPath);
        motorModel = buildMotorModelForSyre(matPath, motPath);
    else
        fprintf('  [경고] MOT 파일 없음 → 하드코딩 기본값으로 빌드합니다.\n');
        motorModel = buildMotorModelForSyre(matPath);
    end

    d = motorModel.data;
    fprintf('\n  --- 추출된 모터 파라미터 ---\n');
    fprintf('    p      (극쌍수)        = %d\n',      d.p);
    fprintf('    Rs0    (DC 상저항)     = %.6f Ohm\n', d.Rs);
    fprintf('    l      (스택길이)      = %.4f m\n',   d.l);
    fprintf('    lend   (엔드와인딩)    = %.4f m\n',   d.lend);
    fprintf('    Vdc    (DC링크전압)    = %.1f V\n',   d.Vdc);
    fprintf('    Imax   (피크전류)      = %.2f A_pk\n', d.Imax);
    fprintf('    nmax   (최대속도)      = %.0f rpm\n', d.nmax);
    fprintf('    tempCu (권선온도)      = %.1f C\n',   d.tempCu);

    % 파라미터 유효성: 모두 유한하고 양수여야 정상
    pv = [d.p, d.Rs, d.l, d.lend, d.Vdc, d.Imax, d.nmax, d.tempCu];
    if any(~isfinite(pv)) || any(pv(1:7) <= 0)
        fprintf('  [실패] 일부 파라미터가 비정상(NaN/Inf/≤0) 입니다.\n');
        step3_ok = false;
    end

    % acLossFactor 빌드 여부
    if isfield(motorModel, 'acLossFactor') && ~isempty(motorModel.acLossFactor)
        fprintf('  → acLossFactor 빌드됨 (type=%s, %d 주파수 포인트)\n', ...
            motorModel.acLossFactor.type, numel(motorModel.acLossFactor.f));
    else
        fprintf('  → acLossFactor 비어있음 (AC손실 데이터 없음 또는 미빌드)\n');
        if hasAcLoss
            fprintf('  [실패] AC손실 데이터가 있는데 acLossFactor 가 비었습니다!\n');
            step3_ok = false;
        end
    end
    fprintf('  → TnSetup.SkinEffectFlag = %s\n', motorModel.TnSetup.SkinEffectFlag);
catch ME
    fprintf('  [실패] buildMotorModelForSyre 에서 에러: %s\n', ME.message);
    step3_ok = false;
end
[nPass, nFail] = bumpCounters(nPass, nFail, ...
    report('STEP 3 (motorModel 빌드)', step3_ok, '파라미터 추출 + acLossFactor'));


%% ───────────────────────────────────────────────────────────────────────
%% STEP 4. buildAcLossFactor 출력 확인 — kAC vs frequency 곡선 플롯
%% ───────────────────────────────────────────────────────────────────────
fprintf('\n========== STEP 4: acLossFactor (kAC vs freq) 플롯 ==========\n');
step4_ok = true;
if isempty(motorModel) || ~isfield(motorModel, 'acLossFactor') || isempty(motorModel.acLossFactor)
    fprintf('  [건너뜀] acLossFactor 가 없어 플롯을 생략합니다.\n');
    step4_ok = hasAcLoss == false;  % AC손실이 애초에 없으면 정상(스킵), 있는데 없으면 STEP3에서 이미 FAIL
    if ~hasAcLoss
        fprintf('  → AC손실 데이터가 없는 모델이므로 정상적인 스킵입니다.\n');
    end
else
    aclf = motorModel.acLossFactor;
    fprintf('  f [Hz]: '); fprintf('%.1f ', aclf.f); fprintf('\n');
    fprintf('  k [ ] : '); fprintf('%.4f ', aclf.k); fprintf('\n');

    % 단조성/물리 제약 검사: kAC >= 1, f 단조증가
    if any(aclf.k < 1 - 1e-9)
        fprintf('  [경고] kAC < 1 인 포인트가 있습니다 (물리적으로 부적절).\n');
        step4_ok = false;
    end
    if any(diff(aclf.f) <= 0)
        fprintf('  [경고] 주파수 벡터가 단조증가가 아닙니다.\n');
        step4_ok = false;
    end

    try
        hfig = figure('Name', 'STEP4: kAC vs Frequency', 'Position', [120 120 560 420]);
        plot(aclf.f, aclf.k, 'o-', 'LineWidth', 1.5, 'MarkerFaceColor', 'auto');
        grid on; xlabel('Electrical Frequency [Hz]'); ylabel('k_{AC} = R_{ac}/R_{dc}');
        title('AC Loss Factor (k_{AC}) vs Frequency');
        yline(1, '--k', 'k_{AC}=1');
        figPath = fullfile(current_dir, 'figures');
        if ~exist(figPath, 'dir'); mkdir(figPath); end
        saveas(hfig, fullfile(figPath, 'phase1_kAC_vs_freq.png'));
        fprintf('  → 플롯 저장: %s\n', fullfile(figPath, 'phase1_kAC_vs_freq.png'));
    catch ME
        fprintf('  [경고] 플롯 생성 중 에러: %s\n', ME.message);
    end
end
[nPass, nFail] = bumpCounters(nPass, nFail, ...
    report('STEP 4 (kAC 곡선)', step4_ok, 'kAC vs frequency 플롯'));


%% ───────────────────────────────────────────────────────────────────────
%% STEP 5. calcSkinEffect 외삽(extrapolation) 테스트
%% ───────────────────────────────────────────────────────────────────────
fprintf('\n========== STEP 5: calcSkinEffect 외삽 테스트 ==========\n');
step5_ok = true;
if isempty(motorModel) || ~isfield(motorModel, 'acLossFactor') || isempty(motorModel.acLossFactor)
    fprintf('  [건너뜀] acLossFactor 가 없어 외삽 테스트를 생략합니다.\n');
    step5_ok = ~hasAcLoss;
else
    aclf = motorModel.acLossFactor;
    fMaxData = max(aclf.f);
    tempCu   = motorModel.data.tempCu;

    % 데이터 범위 밖 고주파수 (예: 3000 Hz 또는 데이터 최대의 2배 중 큰 값)
    fTest = max(3000, 2*fMaxData);
    fprintf('  데이터 최대 주파수 = %.1f Hz, 테스트 주파수 = %.1f Hz (범위 밖)\n', fMaxData, fTest);

    try
        kIn  = calcSkinEffect(aclf, fMaxData, tempCu, 'LUT');   % 범위 내 (참조)
        kOut = calcSkinEffect(aclf, fTest,    tempCu, 'LUT');   % 범위 밖 (외삽)
        fprintf('  kAC(%.0f Hz, 범위내) = %.4f\n', fMaxData, kIn);
        fprintf('  kAC(%.0f Hz, 범위밖) = %.4f\n', fTest, kOut);

        if isnan(kOut)
            fprintf('  [실패] 범위 밖에서 NaN 반환 → extrapolation 패치 미적용?\n');
            step5_ok = false;
        elseif kOut < 1 - 1e-9
            fprintf('  [실패] 외삽값이 1 미만 (물리 제약 위반).\n');
            step5_ok = false;
        else
            fprintf('  → 범위 밖에서도 유한한 kAC(>=1) 반환: extrapolation 정상 동작\n');
        end
    catch ME
        fprintf('  [실패] calcSkinEffect 호출 에러: %s\n', ME.message);
        step5_ok = false;
    end
end
[nPass, nFail] = bumpCounters(nPass, nFail, ...
    report('STEP 5 (외삽 동작)', step5_ok, '범위 밖 주파수 extrapolation'));


%% ───────────────────────────────────────────────────────────────────────
%% STEP 6. MMM_eval_AOA 단독 실행 — MTPA/MTPV 궤적 계산 + 플롯
%% ───────────────────────────────────────────────────────────────────────
fprintf('\n========== STEP 6: MMM_eval_AOA (제어궤적) 실행 ==========\n');
step6_ok = true;
if isempty(motorModel) || ~isstruct(motorModel)
    fprintf('  [건너뜀] motorModel 이 없어 AOA 를 생략합니다.\n');
    step6_ok = false;
else
    try
        % FluxMap_dq 의 비-2D 필드 제거 (mapsReInterpolation 크기비교 에러 방지)
        %   ※ acLossFactor 는 STEP3 에서 이미 빌드됨 → 여기서 제거해도 안전
        non2DFields = {'speed_vec', 'Pac_total_kW', 'Pac_prox_kW', 'Pac_skin_kW'};
        for f = non2DFields
            if isfield(motorModel.FluxMap_dq, f{1})
                motorModel.FluxMap_dq = rmfield(motorModel.FluxMap_dq, f{1});
            end
        end

        fprintf('  MMM_eval_AOA 실행 중...\n');
        motorModel.controlTrajectories = MMM_eval_AOA(motorModel, 'LUT');

        ct = motorModel.controlTrajectories;
        if isempty(ct) || ~isstruct(ct)
            fprintf('  [실패] controlTrajectories 가 비어있습니다.\n');
            step6_ok = false;
        else
            fprintf('  → controlTrajectories 필드: %s\n', strjoin(fieldnames(ct)', ', '));
            % MTPA/MTPV 궤적 플롯 (필드명은 SyRE 버전에 따라 방어적으로 접근)
            try
                hfig = figure('Name', 'STEP6: Control Trajectories (MTPA/MTPV)', ...
                              'Position', [150 150 560 460]);
                hold on; grid on;
                if isfield(ct, 'MTPA') && isfield(ct.MTPA, 'id') && isfield(ct.MTPA, 'iq')
                    plot(ct.MTPA.id, ct.MTPA.iq, 'b-', 'LineWidth', 1.8, 'DisplayName', 'MTPA');
                end
                if isfield(ct, 'MTPV') && isfield(ct.MTPV, 'id') && isfield(ct.MTPV, 'iq')
                    plot(ct.MTPV.id, ct.MTPV.iq, 'r-', 'LineWidth', 1.8, 'DisplayName', 'MTPV');
                end
                xlabel('I_d [A]'); ylabel('I_q [A]');
                title('Control Trajectories (MTPA / MTPV)');
                legend('Location', 'best'); axis equal;
                figPath = fullfile(current_dir, 'figures');
                if ~exist(figPath, 'dir'); mkdir(figPath); end
                saveas(hfig, fullfile(figPath, 'phase1_control_trajectories.png'));
                fprintf('  → 플롯 저장: %s\n', fullfile(figPath, 'phase1_control_trajectories.png'));
            catch MEp
                fprintf('  [경고] 궤적 플롯 중 에러(계산은 성공): %s\n', MEp.message);
            end
        end
    catch ME
        fprintf('  [실패] MMM_eval_AOA 에러: %s\n', ME.message);
        step6_ok = false;
    end
end
[nPass, nFail] = bumpCounters(nPass, nFail, ...
    report('STEP 6 (제어궤적 AOA)', step6_ok, 'MTPA/MTPV 궤적 계산'));


%% ───────────────────────────────────────────────────────────────────────
%% STEP 7. MMM_MaxTw 실행 — 효율맵 연산 완료 확인
%% ───────────────────────────────────────────────────────────────────────
fprintf('\n========== STEP 7: MMM_MaxTw (효율맵) 실행 ==========\n');
step7_ok = true;
if isempty(motorModel) || ~isfield(motorModel, 'controlTrajectories') || isempty(motorModel.controlTrajectories)
    fprintf('  [건너뜀] controlTrajectories 가 없어 효율맵을 생략합니다 (STEP6 실패).\n');
    step7_ok = false;
else
    try
        fprintf('  MMM_MaxTw 실행 중 (헤드리스, 자동저장)...\n');
        % hax=NaN: 개별 figure 팝업 회피, saveFlag=2: questdlg 없이 자동저장
        [TwMap, resFolderOut] = MMM_MaxTw(motorModel, NaN, 2);

        if ~isstruct(TwMap) || ~isfield(TwMap, 'eff')
            fprintf('  [실패] TwMap.eff 가 없습니다.\n');
            step7_ok = false;
        else
            effMax = max(TwMap.eff(:));
            fprintf('  → 효율맵 계산 완료. TwMap.eff 최대값 = %.2f%%\n', effMax*100);
            fprintf('  → 결과 폴더: %s\n', resFolderOut);
            % 효율맵이 물리적으로 타당한 범위인지 (0 < eff <= 1)
            if ~isfinite(effMax) || effMax <= 0 || effMax > 1
                fprintf('  [실패] 최대 효율이 비정상 범위(%.4f)입니다.\n', effMax);
                step7_ok = false;
            end
        end
    catch ME
        fprintf('  [실패] MMM_MaxTw 에러: %s\n', ME.message);
        step7_ok = false;
    end
end
[nPass, nFail] = bumpCounters(nPass, nFail, ...
    report('STEP 7 (효율맵 MaxTw)', step7_ok, 'TwMap 효율맵 연산'));


%% ───────────────────────────────────────────────────────────────────────
%% 최종 요약
%% ───────────────────────────────────────────────────────────────────────
fprintf('\n');
fprintf('#########################################################\n');
fprintf('#  Phase 1 검증 요약: PASS=%d  FAIL=%d  (총 %d 단계)        \n', ...
        nPass, nFail, nPass+nFail);
fprintf('#########################################################\n');
if nFail == 0
    fprintf('  >> 모든 단계 통과! test_syre_efficiency_map.m 전체 실행 준비 완료.\n');
else
    fprintf('  >> 실패한 단계가 있습니다. 위 로그의 [실패] 메시지를 확인하세요.\n');
end
fprintf('\n');


%% ═══════════════════════════════════════════════════════════════════════
%% 로컬 헬퍼 함수
%% ═══════════════════════════════════════════════════════════════════════
function ok = localReport(name, ok, msg)
%LOCALREPORT  PASS/FAIL 한 줄 출력
if ok
    fprintf('  >>>>> [PASS] %-28s — %s\n', name, msg);
else
    fprintf('  >>>>> [FAIL] %-28s — %s\n', name, msg);
end
end

function [nP, nF] = bumpCounters(nP, nF, ok)
%BUMPCOUNTERS  PASS/FAIL 카운터 갱신
if ok
    nP = nP + 1;
else
    nF = nF + 1;
end
end

function out = ternary(cond, a, b)
%TERNARY  간단한 삼항 연산자 대체
if cond
    out = a;
else
    out = b;
end
end
