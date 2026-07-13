function importExternalTxtLabModel(mcad, txtPath, LabBuildData)
%IMPORTEXTERNALTXTLABMODEL Lab Link=Custom + 외부 LabLink.txt 모델 로드 (단일 모델용)
%
%   mcad.importExternalTxtLabModel(mcad, txtPath)
%   mcad.importExternalTxtLabModel(mcad, txtPath, LabBuildData)
%
%   tools/motorCAD/ImportExternalTXTLabModel.m 의 리팩토링판:
%     - 스케일링(ScaledMachineData)/MotorCADGeo 의존 제거 (단일 모델 워크플로우)
%     - LabBuildData 생략 시 defLabBuildData(mcad)로 현재 모델에서 직접 읽어 재적용
%       (동일 모델에 그대로 재설정 → Link 전환 시 빌드 설정 유지 목적)
%
%   시퀀스 (MCADLabManager.processSLLAW 검증 시퀀스와 동일):
%     ElectroLink_MotorLAB='Custom (Advanced)' → SetMotorLABContext
%     → Lab build 설정 재적용 → ClearModelBuild_Lab → LoadExternalModel_Lab(txt)
%
%   주의: 호출 전 필요 시 아래를 별도 설정할 것 (MCADLabManager 흐름 참조)
%     ACLossHighFrequencyScaling_Method=0, CurrentSpec_MotorLAB=0(peak),
%     MaxModelCurrent_MotorLAB=max(table.Is)

assert(isfile(txtPath), 'LabLink txt 없음: %s', txtPath);

if nargin < 3 || isempty(LabBuildData)
    LabBuildData = defLabBuildData(mcad);   % 현재 모델 값 그대로 재적용
end

% Lab Link 타입: 'Motor-CAD EMag' | 'Ansys' | 'Custom (Advanced)'
mcad.SetVariable('ElectroLink_MotorLAB', 'Custom (Advanced)');
mcad.SetMotorLABContext();

% Lab build 설정 재적용 (기존 ImportExternalTXTLabModel와 동일 목록)
mcad.SetVariable('CalcTypeCuLoss_MotorLAB',    LabBuildData.CalcTypeCuLoss_MotorLAB);
mcad.SetVariable('n2ac_MotorLAB',              LabBuildData.n2ac_MotorLAB);
mcad.SetVariable('AcLossFreq_MotorLAB',        LabBuildData.AcLossFreq_MotorLAB);
mcad.SetVariable('IronLossCalc_Lab',           LabBuildData.IronLossCalc_Lab);
mcad.SetVariable('FEALossMap_RefSpeed_Lab',    LabBuildData.FEALossMap_RefSpeed_Lab);
mcad.SetVariable('MagnetLossCalc_Lab',         LabBuildData.MagnetLossCalc_Lab);
mcad.SetVariable('MagLossCoeff_MotorLAB',      LabBuildData.MagLossCoeff_MotorLAB);
mcad.SetVariable('BandingLossCalc_Lab',        LabBuildData.BandingLossCalc_Lab);
mcad.SetVariable('BandingLossCoefficient_Lab', LabBuildData.BandingLossCoefficient_Lab);

mcad.ClearModelBuild_Lab();
mcad.LoadExternalModel_Lab(txtPath);

% read-back 확인
[~, linkType] = mcad.GetVariable('ElectroLink_MotorLAB');
[~, isBuilt]  = mcad.GetModelBuilt_Lab();
fprintf('[importExternalTxtLabModel] Link=%s, ModelBuilt=%d\n  txt: %s\n', ...
    char(linkType), double(isBuilt), txtPath);
if ~strcmpi(strtrim(char(linkType)), 'Custom (Advanced)')
    warning('ElectroLink_MotorLAB read-back이 예상과 다름: %s', char(linkType));
end
end
