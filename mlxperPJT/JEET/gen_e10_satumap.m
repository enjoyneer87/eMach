%% gen_e10_satumap.m
% e10 모터(e10Turn6V261.mot)의 SaturationMap을 계산하여
% tools/SystemSimulationModel/e10_SatuMap.mat 으로 저장하는 스크립트.
%
% [사전조건]
%   - Motor-CAD가 미리 실행 중이어야 함 (actxserver가 실행 중인 인스턴스에 연결)
%   - e10Turn6V261.mot 의 Lab 모델이 정상 빌드된 상태여야 함
%   - eMach 루트가 MATLAB path에 추가되어 있거나, Cell [0] 먼저 실행
%
% [주의] 기존 tools/SystemSimulationModel/SatuMap.mat 은 Tesla Plaid 데이터임.
%        절대 덮어쓰지 말 것. 본 스크립트는 별도 파일 e10_SatuMap.mat 에 저장함.
%
% [SaturationMap_InputDefinition 파라미터 설명]
%   0 = Polar      : 고정자 전류 크기(Is) + 위상 전진각(beta) 격자 기반 계산
%   1 = Cartesian  : d-q 전류(Id/Iq) 격자 기반 계산
%
%   본 스크립트는 InputDefinition=0, nargin=3 형태로 호출하여
%   .mot 파일에 저장된 기존 격자 설정을 그대로 사용함.
%   (nargin==3+InputDef==1 또는 nargin==5 형태는
%    devExportSatuMapFromMCADLabModel 내부 Imaxpk 미정의 버그로 에러 발생 가능)

%% [0] 경로 설정
scriptDir = fileparts(mfilename('fullpath'));          % .../mlxperPJT/JEET
eMachRoot = fullfile(scriptDir, '..', '..');           % .../eMach
addpath(genpath(eMachRoot));

motPath = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot';
outPath = fullfile(eMachRoot, 'tools', 'SystemSimulationModel', 'e10_SatuMap.mat');

fprintf('입력 .mot : %s\n', motPath);
fprintf('출력 .mat : %s\n', outPath);

%% [1] Motor-CAD ActiveX 연결 + .mot 파일 로드
% callMCAD() → actxserver('motorcad.appautomation')
% Motor-CAD가 미리 실행 중이어야 정상 연결됨.
mcad = callMCAD();
mcad.SetVariable('MessageDisplayState', 2);   % 팝업 메시지 억제

if ~isfile(motPath)
    error('mot 파일이 없습니다: %s', motPath);
end
mcad.LoadFromFile(motPath);
fprintf('.mot 로드 완료\n');

[~, isBuilt] = mcad.GetModelBuilt_Lab();
if ~isBuilt
    fprintf('Lab 모델 빌드 중...\n');
    mcad.BuildModel_Lab();
    fprintf('Lab 모델 빌드 완료\n');
else
    fprintf('Lab 모델 이미 빌드됨\n');
end

%% [2] SaturationMap 계산 및 저장
% InputDefinition=0 (Polar), nargin=3 → .mot 격자 설정 그대로 사용
fprintf('SaturationMap 계산 중 (수 분 소요)...\n');
BuildingData = devExportSatuMapFromMCADLabModel(outPath, mcad, 0);
fprintf('저장 완료: %s\n', outPath);

%% [3] 저장 파일 로드 및 구조 확인
loaded = load(outPath);

fprintf('\n=== BuildingData 최상위 필드 ===\n');
disp(fieldnames(loaded.BuildingData));

fprintf('=== satuMapData 필드 및 크기 ===\n');
fn = fieldnames(loaded.BuildingData.satuMapData);
for i = 1:numel(fn)
    val = loaded.BuildingData.satuMapData.(fn{i});
    if isnumeric(val)
        fprintf('  %-35s  size: %s\n', fn{i}, mat2str(size(val)));
    end
end

Imaxpk_e10 = loaded.BuildingData.MotorCADGeo.Imaxpk;
Vdc_e10    = loaded.BuildingData.MotorCADGeo.DCBusVoltage;
fprintf('\nImaxpk = %.1f A,  Vdc = %.1f V\n', Imaxpk_e10, Vdc_e10);
