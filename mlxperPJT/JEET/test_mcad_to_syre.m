% test_mcad_to_syre.m
% Motor-CAD Lab → SyRE FluxMap_dq 변환 검증 스크립트
% 두 가지 워크플로우를 모두 테스트합니다.

emach_root = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(genpath(emach_root));
addpath(genpath('D:\KangDH\gitSyREpub\syre_public'));

motPath  = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot';
jsonPath = 'D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports\e10\Ref\JEET_ACLoss_Ref_Map_Summary.json';
p        = 4;
n0_rpm   = 500;   % Lab FEA 철손 맵 기준 속도

% ═══════════════════════════════════════════════════════════════════════════════
% 워크플로우 A — fromMCAD_lab_json  (6×8 → linspace 격자)
% ═══════════════════════════════════════════════════════════════════════════════
% fprintf('\n══ Workflow A: fromMCAD_lab_json ══\n');
% outMat_A = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261_SyreMMM_A.mat';
%
% out_A = mcad.fromMCAD_lab_json(motPath, jsonPath, p);
% mcad.saveSyreFluxMap(out_A, outMat_A);
%
% motorModel_A = buildMotorModel(out_A, outMat_A);
% MMM_plot_fdfq(motorModel_A);
% if isfield(motorModel_A, 'IronPMLossMap_dq')
%     MMM_plot_ironLoss(motorModel_A);
% end

% ═══════════════════════════════════════════════════════════════════════════════
% 워크플로우 B — fromFitResult  (100×100, scatteredInterpolant)
% ═══════════════════════════════════════════════════════════════════════════════
fprintf('\n══ Workflow B: fromFitResult ══\n');
outMat_B = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261_SyreMMM_B.mat';

filteredTable = getMCADLabDataFromMotFile(motPath);
MCADLinkTable = reNameLabTable2LabLink(filteredTable);
FitResultStr  = plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable, 'bilinear'); % emach기존 Fitting Function

out_B = mcad.fromFitResult(FitResultStr, p, jsonPath, n0_rpm); % +mcad 함수를 통한 syre 데이터포맷 연동
mcad.saveSyreFluxMap(out_B, outMat_B);

motorModel_B = buildMotorModel(out_B, outMat_B);
MMM_plot_fdfq(motorModel_B);
if isfield(motorModel_B, 'IronPMLossMap_dq')
    MMM_plot_ironLoss(motorModel_B);
end

fprintf('\n완료. B: %s\n', outMat_B);

% ── MTPA 검증 (Is,Gamma 보간 후 kink 해소 확인) ──────────────────────────────
fprintf('\n── MTPA 계산 (LUT) ──\n');
motorModel_B.controlTrajectories = MMM_eval_AOA(motorModel_B, 'LUT');
MMM_plot_MTPA(motorModel_B);


% ── 공통 메타데이터 ───────────────────────────────────────────────────────────
function motorModel = buildMotorModel(out, outMat)
    motorModel = struct();
    motorModel.FluxMap_dq = out.FluxMap_dq;
    if isfield(out, 'IronPMLossMap_dq')
        motorModel.IronPMLossMap_dq = out.IronPMLossMap_dq;
    end
    motorModel.data.motorType = 'PM';
    motorModel.data.pathname  = [fileparts(outMat) filesep];
    motorModel.data.motorName = 'e10Turn6V261';
    motorModel.data.tempPM    = 80;
    motorModel.data.n0        = 4419;
    motorModel.data.nmax      = 18000;
    motorModel.data.axisType  = 'dq';   % SyRE PM 모터 기본 축 규약
end