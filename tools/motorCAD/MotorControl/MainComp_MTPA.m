% function compMTPAFromMCADTable(target_Tload,Vlim,MCADLinkTable,MachineData,nTargetList)
%% 전반적인 수정필요
MotFilePath=getCurrentMCADFilePath(mcad(1))

modifiedDataStruct=getMcadActiveXTableFromMotFile(MotFilePath)
filteredTable=getMCADLabDataFromMotFile(MotFilePath)

%
originLabLinkTable = reNameLabTable2LabLink(filteredTable);
MCADLinkTable=originLabLinkTable

%% EEC LUT_PMSM (Comp_MTPA)
% 최적의 전류를 찾기 위한 함수
% target_Tload: 목표 부하 토크
% Vlim: 전압 제한
% MCADLinkTable: MCAD 링크 테이블
% MachineData: 기계 데이터
% nTarget: 목표 속도

%% prepare the data & Create Sfit
[FluxLinkDFit,~,~]                         =createInterpDataSet(MCADLinkTable,'Flux Linkage D');
[FluxLinkQFit,~,~]                         =createInterpDataSet(MCADLinkTable,'Flux Linkage Q');
[LdFitResult, LqFitResult,PMFit2DResult,~] = fitLdLqMapsFromMCADTable(MCADLinkTable);
%McadLink Table 에서 손실 interpolation 함수 생
% 데이터와 속도 목록
nTargetList = [1000, 2000, 8000 15000]; % rpm
[Ploss_dqh, SpeedScaledInfo] = interpLossFitResultSpeedFromMcadTable(MCADLinkTable, MachineData, nTargetList);


% EECLUTdq 객체 배열 초기화 및 생성
EECLUTdqArray = EECLUTdq.empty(length(nTargetList), 0);  % 빈 배열로 초기화

% 각 타겟 속도에 대한 EECLUTdq 객체 생성
for k = 1:length(nTargetList)
    omegaE = freq2omega(SpeedScaledInfo(k).freqEOp);  % Convert frequency to angular frequency
    EECLUTdqArray(k) = EECLUTdq(FluxLinkDFit, FluxLinkQFit, LdFitResult, LqFitResult, PMFit2DResult, Ploss_dqh(k).fitResult, omegaE,SpeedScaledInfo(k), MachineData.MotorCADGeo.Pole_Number);
    
end

%% 
k=4
[idm_rms_opt, iqm_rms_opt, id_rms, iq_rms, eeclutdq_out]  = findOptimalCurrentsWithConstraints(438.2, 720*0.97,  EECLUTdqArray(k),MCADLinkTable);

TShaft = eeclutdq_out.TShaft;
Vs_pk = eeclutdq_out.Vs_pk;


Im_rms=[-315.7,334.6]
Im_rmsAmp=sqrt(Im_rms(1)^2+Im_rms(2)^2)
[pk,beta]=dq2pkBeta(rms2pk(idm_rms_opt),rms2pk(iqm_rms_opt))
beta-90
Im_rms=[idm_rms_opt,iqm_rms_opt]

 % EECLUTdqArray(k)=updateElecLossData(EECLUTdqArray(k), Im_rms)
idm_pk=rms2pk(idm_rms_opt);
iqm_pk=rms2pk(iqm_rms_opt);
Ld=eeclutdq_out.LdFitResult(idm_pk,iqm_pk)
Lq=eeclutdq_out.LqFitResult(idm_pk,iqm_pk)
psi_PM=eeclutdq_out.PMFitResult(idm_pk,iqm_pk)

lambdaD = eeclutdq_out.LambdaDFit(idm_pk, iqm_pk);
lambdaQ = eeclutdq_out.LambdaQFit(idm_pk, iqm_pk);

TorqueDQ =calcDQFluxTorque(idm_rms_opt, iqm_rms_opt, lambdaD,lambdaQ,eeclutdq_out.PoleNumber)
TorqueDQ-eeclutdq_out.lastElecLossData.TorqueElecLossWODCLoss
calcDQLTorque(idm_rms_opt,iqm_rms_opt,8,psi_PM,Ld,Lq)-eeclutdq_out.lastElecLossData.TorqueElecLossWODCLoss
