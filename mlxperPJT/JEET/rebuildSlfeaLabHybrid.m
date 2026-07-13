%% rebuildSlfeaLabHybrid.m
% e10Turn6V261SLFEA.mot의 Lab 모델을 지우고 Emag 스윕(json) 격자에 맞춰 재빌드
%
%   - 대상: D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot (customLoss 사본 아님)
%   - CalcTypeCuLoss_MotorLAB = 1 (Hybrid)   ← 기존 3(FEA map)에서 변경
%   - CurrentSpec=1(RMS), MaxModelCurrent_RMS = 920 Arms (= json 스윕 최대전류)
%   - ModelBuildPoints: Current=5, Gamma=6   (= json 격자 [0..920]×5, [0..90]×6)
%
% 실행 전 .mot 타임스탬프 백업 생성. 빌드 후 저장 + .mot 재파싱으로 격자 확인.

%% [0] 경로
scriptDir = fileparts(mfilename('fullpath'));
eMachRoot = fullfile(scriptDir, '..', '..');
addpath(genpath(eMachRoot));

slfeaMot = 'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA.mot';
assert(isfile(slfeaMot), '.mot 없음: %s', slfeaMot);

% 백업 (최초 1회)
bakPath = strrep(slfeaMot, '.mot', '_beforeHybridRebuild.mot');
if ~isfile(bakPath)
    copyfile(slfeaMot, bakPath);
    fprintf('[0] 백업 생성: %s\n', bakPath);
else
    fprintf('[0] 백업 이미 존재: %s\n', bakPath);
end

%% [1] Motor-CAD 연결 (실행 중 인스턴스 재사용, 없으면 새로 실행) + v261 가드
try
    clsid  = winqueryreg('HKEY_CLASSES_ROOT', 'motorcad.appautomation\CLSID');
    try
        comExe = winqueryreg('HKEY_LOCAL_MACHINE', ...
            ['SOFTWARE\WOW6432Node\Classes\CLSID\' clsid '\LocalServer32']);
    catch
        comExe = winqueryreg('HKEY_LOCAL_MACHINE', ...
            ['SOFTWARE\Classes\CLSID\' clsid '\LocalServer32']);
    end
    fprintf('[1] COM 서버: %s\n', comExe);
    assert(contains(comExe, 'v261'), 'COM 등록이 v261이 아님: %s', comExe);
catch e
    warning('COM 등록 확인 실패: %s', e.message);
end

try
    mcad = actxGetRunningServer('motorcad.appautomation');
    fprintf('[1] 실행 중인 Motor-CAD 인스턴스에 연결\n');
catch
    mcad = actxserver('motorcad.appautomation');
    fprintf('[1] 새 Motor-CAD 인스턴스 실행\n');
end
mcad.SetVariable('MessageDisplayState', 2);   % 팝업 억제 (GUI 표시 유지)

mcad.LoadFromFile(slfeaMot);
fprintf('[1] 로드: %s\n', slfeaMot);

%% [2] 기존 Lab 빌드 제거 + 빌드 설정 (json 격자 정렬, Hybrid)
mcad.SetMotorLABContext();
mcad.ClearModelBuild_Lab();
fprintf('[2] 기존 Lab 모델 클리어\n');

mcad.SetVariable('CalcTypeCuLoss_MotorLAB',      1);     % 1 = Hybrid
mcad.SetVariable('CurrentSpec_MotorLAB',         1);     % 1 = RMS 입력
mcad.SetVariable('MaxModelCurrent_RMS_MotorLAB', 920);   % json 최대전류 [Arms]
mcad.SetVariable('ModelBuildPoints_Current_Lab', 5);
mcad.SetVariable('ModelBuildPoints_Gamma_Lab',   6);

% read-back 검증
chk = {'CalcTypeCuLoss_MotorLAB', 'CurrentSpec_MotorLAB', ...
       'MaxModelCurrent_RMS_MotorLAB', 'MaxModelCurrent_MotorLAB', ...
       'ModelBuildPoints_Current_Lab', 'ModelBuildPoints_Gamma_Lab', ...
       'n2ac_MotorLAB', 'FEALossMap_RefSpeed_Lab', 'AcLossFreq_MotorLAB'};
fprintf('[2] 설정 read-back:\n');
for v = chk
    [~, val] = mcad.GetVariable(v{1});
    fprintf('    %-32s = %s\n', v{1}, num2str(double(val)));
end

%% [3] Lab 빌드 (수 분~수십 분 소요 가능)
fprintf('[3] BuildModel_Lab 시작 ... %s\n', char(datetime('now')));
tBuild = tic;
mcad.BuildModel_Lab();
fprintf('[3] 빌드 완료 (%.1f분)\n', toc(tBuild)/60);

[~, isBuilt] = mcad.GetModelBuilt_Lab();
fprintf('[3] GetModelBuilt_Lab = %d\n', double(isBuilt));
assert(double(isBuilt) == 1, 'Lab 빌드 실패');

mcad.SaveToFile(slfeaMot);
fprintf('[3] 저장 완료: %s\n', slfeaMot);

%% [4] 저장된 .mot 재파싱으로 격자/데이터 확인
T = getMCADLabDataFromMotFile(slfeaMot);
fprintf('\n[4] 재파싱 확인: %d 운전점 × %d 변수\n', height(T), width(T));
IsU  = unique(T.SatModel_Is_Lab);
GamU = unique(T.SatModel_Gamma_Lab);
fprintf('    Is    %d점: %s [Apk] (920Arms=1301.1Apk 기대)\n', numel(IsU), mat2str(round(IsU', 1)));
fprintf('    Gamma %d점: %s [deg]\n', numel(GamU), mat2str(GamU'));
if ismember('Stator_Copper_Loss_AC', T.Properties.VariableNames)
    fprintf('    Stator_Copper_Loss_AC 범위: %.4g ~ %.4g W\n', ...
        min(T.Stator_Copper_Loss_AC), max(T.Stator_Copper_Loss_AC));
end
fprintf('\n>> 다음: verifyLabVsEmag_e10.m 재실행으로 새 Lab 테이블 vs SC json 재검증 <<\n');
