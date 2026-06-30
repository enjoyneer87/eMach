% test_syre_efficiency_map.m
% -------------------------------------------------------------------------
% run_efficiency_map.py 등에서 생성한 .mat 파일을 로드하여
% SyRE MMM(calcTnPoint / calcOptCtrl) 엔진으로 최적 전류위상각을 탐색하고
% 효율맵을 계산하여 플로팅하는 매틀랩 검증 스크립트.
% -------------------------------------------------------------------------

clc; clear; close all;

%% 1. 경로 설정
current_dir = fileparts(mfilename('fullpath'));
emach_root  = fileparts(fileparts(current_dir));

addpath(genpath(emach_root));
addpath(genpath('D:\KangDH\gitSyREpub\syre_public'));

%% 2. 타겟 모델 목록 설정 (Ref, HalfSC, SC)
% 파이썬에서 빌드하여 내보낸 각 모델의 MAT 파일 경로
motPath = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot';
filteredTable = getMCADLabDataFromMotFile(motPath);
MCADLinkTable  = reNameLabTable2LabLink(filteredTable);

matFiles = {
    'D:\KangDH\Thesis\e10\refModel\e10Turn6V261_FluxMap_Py.mat'  % Ref/SC/HalfSC 통합 또는 개별 파일
    'D:\KangDH\Thesis\e10\refModel\e10Turn6V261_SyreMMM_B.mat'   % MATLAB 워크플로우 B 결과
};

% 테스트로 워크플로우 B 결과 파일(_B.mat)을 로드하여 실행해봅니다.
targetMat = matFiles{2}; 
fprintf('==================================================\n');
fprintf('Loading SyRE MMM Model File: \n%s\n', targetMat);
fprintf('==================================================\n');

if ~exist(targetMat, 'file')
    error('대상 MAT 파일이 존재하지 않습니다: %s', targetMat);
end

%% 3. motorModel 구조체 빌드
motorModel = buildMotorModelForSyre(targetMat);

%% 4. 최적 제어 궤적(MTPA, MTPV) 사전 연산
fprintf('\nEvaluating Control Trajectories (MTPA / MTPV) via SyRE AOA...\n');

% FluxMap_dq에서 2D 그리드 크기와 다른 임의 차원의 필드들을 제거하여
% SyRE 내장 함수인 mapsReInterpolation의 크기 비교(==) 에러를 방지합니다.
non2DFields = {'speed_vec', 'Pac_total_kW', 'Pac_prox_kW', 'Pac_skin_kW'};
for f = non2DFields
    if isfield(motorModel.FluxMap_dq, f{1})
        motorModel.FluxMap_dq = rmfield(motorModel.FluxMap_dq, f{1});
    end
end

motorModel.controlTrajectories = MMM_eval_AOA(motorModel, 'LUT');

%% 5. SyRE MMM 효율맵 연산 엔진 실행 (MMM_MaxTw)
fprintf('\nEvaluating Efficiency Map on Speed-Torque Grid (Max efficiency)...\n');
% saveFlag = 2: dialog questdlg 팝업 없이 결과를 자동으로 mat 파일에 저장
% hax = NaN: 헤드리스 실행 및 개별 피규어 그리기 팝업 회피
[TwMap, resFolderOut] = MMM_MaxTw(motorModel, NaN, 2);

%% 6. 결과 출력 및 비교 검증
fprintf('\n==================================================\n');
fprintf('SyRE Evaluation Complete!\n');
fprintf('Results saved in: %s\n', resFolderOut);
fprintf('Max Efficiency (SyRE): %.2f%%\n', max(TwMap.eff(:)) * 100);
fprintf('==================================================\n');


% plot 

MMM_plot_fdfq(motorModel)  
MMM_plot_ironLoss(motorModel)
MMM_plot_skinEffect(motorModel);
MMM_plot_MTPA(motorModel);


%% 7. Python 계산 결과와 SyRE 계산 결과 통합 비교 플롯
% run_eff_map_single.py 가 생성하는 단일모델(Ref) 결과 파일을 사용한다.
% (efficiency_map_results.mat 은 별도 run_efficiency_map.py 의 Ref/HalfSC/SC
%  3모델 산출물로, 이 파이프라인의 단계 2와 무관하므로 사용하지 않는다.)
python_results_path = fullfile(current_dir, 'eff_map_single_ref.mat');
if ~exist(fullfile(current_dir, 'figures'), 'dir')
    mkdir(fullfile(current_dir, 'figures'));
end

effLevels = [64:2:86 87:1:100]/100;

% --- SyRE 단독 효율맵 ---
hfig2 = figure('Name', 'SyRE Calculated Efficiency Map', 'Position', [200, 200, 600, 450]);
[c, h] = contourf(TwMap.n, TwMap.T, TwMap.eff, effLevels, 'ShowText', 'on');
clabel(c, h, 'FontSize', 8);
colorbar;
title(sprintf('SyRE MMM Max Efficiency Map (Max: %.2f%%)', max(TwMap.eff(:)) * 100));
xlabel('Speed (rpm)');
ylabel('Torque (Nm)');
grid on;

syre_png = fullfile(current_dir, 'figures', 'syre_eff_map_ref.png');
saveas(hfig2, syre_png);
fprintf('Saved SyRE efficiency map plot to: %s\n', syre_png);

if exist(python_results_path, 'file')
    fprintf('\nLoading Python Efficiency Map Results from: \n%s\n', python_results_path);
    py = load(python_results_path);

    [py_nmap, py_Tmap] = meshgrid(py.speed_rpm, py.torque_nm);

    % --- Python(Ref) vs SyRE 효율맵 나란히 비교 ---
    hfig_cmp = figure('Name', 'Python vs SyRE Efficiency Map Comparison', 'Position', [100, 100, 1000, 450]);

    subplot(1, 2, 1);
    eta = py.eta_pct / 100.0;  % pu 단위로 환산
    [c, h] = contourf(py_nmap, py_Tmap, eta, effLevels, 'ShowText', 'on');
    clabel(c, h, 'FontSize', 8);
    colorbar;
    title(sprintf('Python Ref (Max: %.2f%%)', max(py.eta_pct, [], 'all')));
    xlabel('Speed (rpm)');
    ylabel('Torque (Nm)');
    grid on;

    subplot(1, 2, 2);
    [c, h] = contourf(TwMap.n, TwMap.T, TwMap.eff, effLevels, 'ShowText', 'on');
    clabel(c, h, 'FontSize', 8);
    colorbar;
    title(sprintf('SyRE MMM Max Efficiency Map (Max: %.2f%%)', max(TwMap.eff(:)) * 100));
    xlabel('Speed (rpm)');
    ylabel('Torque (Nm)');
    grid on;

    cmp_png = fullfile(current_dir, 'figures', 'python_eff_maps_comparison.png');
    saveas(hfig_cmp, cmp_png);
    fprintf('Saved Python vs SyRE comparison plot to: %s\n', cmp_png);

    % --- AC 동손 Figure (Ref) ---
    hfig_ac = figure('Name', 'AC Copper Loss (Ref)', 'Position', [100, 100, 600, 450]);
    [c, h] = contourf(py_nmap, py_Tmap, py.loss_cu_ac_kW, 'ShowText', 'on');
    clabel(c, h, 'FontSize', 8);
    colorbar;
    title(sprintf('AC Cu Loss Ref (Max: %.2f kW)', max(py.loss_cu_ac_kW, [], 'all')));
    xlabel('Speed (rpm)');
    ylabel('Torque (Nm)');
    grid on;

    ac_png = fullfile(current_dir, 'figures', 'ac_loss_comparison.png');
    saveas(hfig_ac, ac_png);
    fprintf('Saved AC loss comparison plot to: %s\n', ac_png);
else
    warning('Python 결과 파일을 찾을 수 없습니다: %s', python_results_path);
end

% Figure 정리 및 표시
if ~isdeployed && exist('centerAllFigures', 'file')
    centerAllFigures(1);
end
% 
% 
% %% ═══════════════════════════════════════════════════════════════════════════════
% %% 하위 함수: SyRE 호환 motorModel 구조체 초기화
% %% ═══════════════════════════════════════════════════════════════════════════════
% function motorModel = buildMotorModelForSyre(matPath)
%     m = load(matPath);
%     motorModel = struct();
%     motorModel.FluxMap_dq = m.FluxMap_dq;
%     if isfield(m, 'IronPMLossMap_dq')
%         motorModel.IronPMLossMap_dq = m.IronPMLossMap_dq;
%     end
% 
%     % 1) 기본 모터 하드웨어 파라미터 설정
%     motorModel.data.motorType = 'PM';
%     motorModel.data.axisType  = 'PM';
%     motorModel.data.pathname  = [fileparts(matPath) filesep];
% 
%     [~, name, ~] = fileparts(matPath);
%     motorModel.data.motorName = name;
%     motorModel.data.p         = 4;          % 극쌍수 (e10 = 8P -> p=4)
%     motorModel.data.Rs        = 0.063783;   % Stator DC resistance at 20C (Ohm)
%     motorModel.data.n0        = 500;
%     motorModel.data.nmax      = 16000;
%     motorModel.data.Imax      = 650.54;     % Peak Phase Current (460 * sqrt(2) A_pk)
%     motorModel.data.Vdc       = 720;        % DC Link Voltage (V_pk_max * sqrt(3) V)
%     motorModel.data.tempCu    = 20;         % Target temp for Rs (20 C)
%     motorModel.data.tempPM    = 80;
%     motorModel.data.n3phase   = 1;
%     motorModel.data.l         = 0.150;      % Active stack length [m] (e10 = 150mm)
%     motorModel.data.lend      = 0.040;      % End winding length [m] (40mm)
%     motorModel.dataSet.TypeOfRotor = 'PM';
%     motorModel.dataSet.RatedCurrent = 460;
%     motorModel.dataSet.NumOfPolePairs = 4;
%     motorModel.dataSet.Rs = 0.063783;
%     motorModel.dataSet.TargetCopperTemp = 20;
%     motorModel.dataSet.tempPP = 80;
%     motorModel.dataSet.TurnsInSeries = 1;
%     motorModel.dataSet.StackLength = 0.150;
%     motorModel.dataSet.EndWindingsLength = 0.040;
%     motorModel.dataSet.StatorOuterRadius = 1;
% 
%     % 2) scaleFactors / skewData (스케일링/스큐 미적용 기본값)
%     motorModel.tmpScale.Lld = 0;
%     motorModel.tmpScale.Llq = 0;
%     motorModel.tmpScale.Ns  = 1;
%     motorModel.tmpScale.l   = 1;
%     motorModel.tmpScale.R   = 1;
%     motorModel.tmpSkew.thSkw = 0;
%     motorModel.tmpSkew.nSlice = 1;
%     motorModel.tmpSkew.nPoints = 51;
% 
%     % 3) TnSetup (Tw) 효율맵 분석 조건 설정
%     Tw.nCurrent         = 1;
%     Tw.nmin             = 0;
%     Tw.nmax             = 16000;
%     Tw.nstep            = 17;        % 속도 17포인트
%     Tw.Tmin             = 0;
%     Tw.Tmax             = 500;
%     Tw.Tstep            = 21;        % 토크 21포인트
%     Tw.temperature      = 20;
%     Tw.MechLoss         = 0;
%     if isfield(m, 'IronPMLossMap_dq')
%         Tw.IronLossFlag   = 'Yes';
%         Tw.PMLossFlag     = 'Yes';
%     else
%         Tw.IronLossFlag   = 'No';
%         Tw.PMLossFlag     = 'No';
%     end
%     Tw.IronLossFactor   = 1;
%     Tw.PMLossFactor     = 1;
%     Tw.SkinEffectFlag   = 'No';
%     Tw.SkinEffectMethod = 'LUT';
%     Tw.Control          = 'Max efficiency'; % 최대 효율 제어 법칙 탐색
%     Tw.ASCsafeFlag      = 'No';
% 
%     motorModel.TnSetup = Tw;
% 
%     % 4) 기본 플레이스홀더 설정
%     motorModel.FluxMap_dqt         = [];
%     motorModel.acLossFactor        = [];
%     motorModel.DemagnetizationLimit = [];
%     motorModel.controlTrajectories = [];
%     motorModel.IncInductanceMap_dq = [];
%     motorModel.FluxMapInv_dq       = [];
%     motorModel.FluxMapInv_dqt      = [];
%     motorModel.SyreDrive           = [];
%     motorModel.WaveformSetup       = [];
%     motorModel.dataSet.pShape.rotor  = [];
%     motorModel.dataSet.pShape.stator = [];
%     motorModel.dataSet.pShape.magnet = [];
%     motorModel.dataSet.pShape.slot   = [];
%     motorModel.dataSet.pShape.flag   = 0;
%     motorModel.dataSet.custom        = 0;
% end
