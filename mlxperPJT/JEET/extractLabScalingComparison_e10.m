%% extractLabScalingComparison_e10.m
% Fig 11 데이터 소스: .mot에 내장된 Lab 빌드 테이블을 직접 추출해
% SCL-M 스케일링 코드(scaleTable4LabTable)를 적용하고, 실측 SC Lab
% 테이블과 나란히 저장한다.
%
% 핵심 성질: Lab 빌드 진폭 격자가 정확히 비례(SC Is = 2 x Ref Is)하므로
% gamma가 겹치는 노드(0, 90 deg)에서는 보간이 전혀 없는 순수 비교가 된다.
%
% 산출: lab_scaling_comparison_e10.mat
%   ref/scaled/sc 각각 Is, Gamma, Id_Peak, Iq_Peak, PsiD, PsiQ [+손실]
%
% 사용 함수(기존 스케일링 워크플로): getMCADLabDataFromMotFile,
% getMCADBuildingDataFromMotFile, reNameLabTable2LabLink,
% scaleTable4LabTable

scriptDir = fileparts(mfilename('fullpath'));
eMachRoot = fullfile(scriptDir, '..', '..');
addpath(genpath(eMachRoot));

% Lab30 (2026-07-30): both LABs rebuilt on the unified 30-point grid
% (6 currents x 5 gammas, grid mode SatModelPoints_MotorLAB=2) so the
% manuscript's "MS-FEA 30 points" and the saturation build coincide.
% I_SC = 2 x I_Ref exactly -> all 30 nodes grid-coincident with the
% scaled-Ref table, zero interpolation in the Fig 9 comparison.
% (Lab48-era paths kept in git history; old mat archived as *_lab48.mat)
refMot = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261_Lab30.mot';
scMot  = 'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_Lab30.mot';
outMat = fullfile(scriptDir, 'map_exports', 'e10', ...
                  'lab_scaling_comparison_e10.mat');

assert(isfile(refMot), 'Ref .mot 없음: %s', refMot);
assert(isfile(scMot),  'SC .mot 없음: %s', scMot);

%% [1] .mot에서 Lab 빌드 테이블 직접 추출 (파싱, COM 불필요)
fprintf('=== [1] Lab 테이블 추출 ===\n');
Tref = getMCADLabDataFromMotFile(refMot);
Tsc  = getMCADLabDataFromMotFile(scMot);
fprintf('Ref: %d pts (Is max %.1f Apk), SC: %d pts (Is max %.1f Apk)\n', ...
    height(Tref), max(Tref.SatModel_Is_Lab), ...
    height(Tsc),  max(Tsc.SatModel_Is_Lab));

%% [2] SCL-M 스케일링 법칙 적용 (scaleTable4LabTable의 법칙과 동일)
% 전체 scaleTable4LabTable 호출은 SLScaleMachine(기계데이터·저항)이 COM
% 형상 전량을 요구하므로, 여기서는 그 함수의 테이블 스케일링 법칙만을
% 그대로 적용한다 (라인 번호는 scaleTable4LabTable.m 기준):
%   전류      I   x k_Radial/k_Winding          (L57)
%   쇄교자속  Psi x k_Winding*k_Radial*k_Axial  (L71, Psi_ew=0)
%   AC 동손       x k_Radial^4*k_Axial          (L106, 동일온도)
%   철손          x k_Radial^2*k_Axial          (L129)
%   자석손        x k_Radial^4*k_Axial          (L115)
fprintf('=== [2] SCL-M 테이블 스케일링 (k_r=2, k_a=1, k_w=1) ===\n');
TrefL = reNameLabTable2LabLink(Tref);
TscL  = reNameLabTable2LabLink(Tsc);

KR = 2.0; KA = 1.0; KW = 1.0;
Tscaled = TrefL;
vn = Tscaled.Properties.VariableNames;

curCols = vn(( contains(vn, 'Is') | contains(vn, 'Id_') ...
             | contains(vn, 'Iq_')) & ~contains(vn, 'Angle'));
for c = curCols
    Tscaled.(c{1}) = (KR / KW) * TrefL.(c{1});
end
fluxCols = vn(contains(vn, 'Flux Linkage') | startsWith(vn, 'Psi'));
for c = fluxCols
    Tscaled.(c{1}) = KW * KR * KA * TrefL.(c{1});
end
acCols = vn(contains(vn, 'AC Copper') ...
            | strcmp(vn, 'Stator_Copper_Loss_AC'));
for c = acCols
    Tscaled.(c{1}) = KR^4 * KA * TrefL.(c{1});
end
feCols = vn(contains(vn, 'Fe') | contains(vn, 'Iron'));
for c = feCols
    Tscaled.(c{1}) = KR^2 * KA * TrefL.(c{1});
end
magCols = vn(contains(vn, 'MagLoss') | contains(vn, 'Magnet Loss'));
for c = magCols
    Tscaled.(c{1}) = KR^4 * KA * TrefL.(c{1});
end

disp(Tscaled.Properties.VariableNames');

%% [3] 저장 (Python 그림/검증용 평면 배열)
% Id/Iq는 리네임 과정에서 빠지므로 원본 테이블(pkgamma2dq 계산값)에서 취함
vn = Tscaled.Properties.VariableNames;
fdName = vn{contains(vn, 'Flux Linkage D')};
fqName = vn{contains(vn, 'Flux Linkage Q')};
gaName = vn{contains(vn, 'Current Angle') | contains(vn, 'Gamma')};

refS = struct('Is', TrefL.Is, 'Gamma', TrefL.(gaName), ...
    'Id_pk', Tref.Id_Peak, 'Iq_pk', Tref.Iq_Peak, ...
    'PsiD', TrefL.(fdName), 'PsiQ', TrefL.(fqName));
scaledS = struct('Is', Tscaled.Is, 'Gamma', Tscaled.(gaName), ...
    'Id_pk', (KR / KW) * Tref.Id_Peak, ...
    'Iq_pk', (KR / KW) * Tref.Iq_Peak, ...
    'PsiD', Tscaled.(fdName), 'PsiQ', Tscaled.(fqName));
scS = struct('Is', TscL.Is, 'Gamma', TscL.(gaName), ...
    'Id_pk', Tsc.Id_Peak, 'Iq_pk', Tsc.Iq_Peak, ...
    'PsiD', TscL.(fdName), 'PsiQ', TscL.(fqName));

save(outMat, 'refS', 'scaledS', 'scS', '-v7');
fprintf('저장: %s\n', outMat);

%% [4] 노드-정확(무보간) 비교: gamma가 양쪽 격자에 공통인 노드
fprintf('=== [4] 노드-정확 비교 (보간 0) ===\n');
tolI = 0.5; tolG = 0.01;
nHit = 0; devD = []; devQ = [];
for i = 1:numel(scS.Is)
    j = find(abs(scaledS.Is - scS.Is(i)) < tolI & ...
             abs(scaledS.Gamma - scS.Gamma(i)) < tolG);
    if isempty(j), continue; end
    j = j(1); nHit = nHit + 1;
    devD(end+1) = scaledS.PsiD(j) - scS.PsiD(i); %#ok<SAGROW>
    devQ(end+1) = scaledS.PsiQ(j) - scS.PsiQ(i); %#ok<SAGROW>
    fprintf(['  Is=%7.1f g=%4.1f | PsiD sc/scaled %+.5f/%+.5f (d=%+.2e)' ...
             ' | PsiQ %+.5f/%+.5f (d=%+.2e)\n'], ...
        scS.Is(i), scS.Gamma(i), scS.PsiD(i), scaledS.PsiD(j), devD(end), ...
        scS.PsiQ(i), scaledS.PsiQ(j), devQ(end));
end
fprintf('공통 노드 %d개: |dPsiD| mean %.3f mVs / |dPsiQ| mean %.3f mVs\n', ...
    nHit, mean(abs(devD))*1e3, mean(abs(devQ))*1e3);
psiScale = max(abs(scS.PsiQ));
fprintf('상대(최대 PsiQ 기준): PsiD %.3f%%  PsiQ %.3f%%\n', ...
    mean(abs(devD))/psiScale*100, mean(abs(devQ))/psiScale*100);
