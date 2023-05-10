% Full Fea For Ac Loss

mcad = actxserver('MotorCAD.AppAutomation');

%Define Input
inputobj=HDEVMotorCADTemp65

%
inputobj.file_name='HDEVMotorCADTemp65FullFeaACLoss'
refProj=strcat(inputobj.file_path,'\',inputobj.refFile,'.mot');
proj=strcat(inputobj.file_path,'\',inputobj.file_name,'.mot');
mcad.LoadFromFile(refProj);


mcad.SaveToFile(proj); % 파일 생성
mcad.LoadFromFile(proj);



%% Magnetic

mcad.SetVariable('MagneticSolver',MagneticSolver)
MagneticSolver 
ACLossGeneratorMethod_Lab
ACLossSpeedScalingMethod_Lab
ACLoss TemperatureScalingMethod
ACLosses_BundleAspectRatio
ACLosses_BundleHeight
ACLosses_BundleWidth
ACLosses_IncludeBundleEffect
AcLossFreq_MotorLAB
CurrentMotFilePath_MotorLAB
HairpinACLossLocationMethod
HybridACLossMethod
HybridAdjustmentFactor_ACLosses
LabModel_ACLoss_Date
LabModel_ACLoss_Method
LabModel_ACLoss_RotorCurrent
LabModel_ACLoss_StatorCurrent_Peak
LabModel_ACLoss_StatorCurrent_RMS
ResultsPath_MotorLAB
WindingTemp_ACLoss_Ref_Lab
%% Method
%%% Lab
ACConductorLossSplit_Lab
'ACConductorLossSplit_Lab'


%% Lab Scailing
ACLossSpeedScalingMethod_Lab
ACLossTemperatureScalingMethod


'ACLossSpeedScalingMethod_Lab'
'ACLossTemperatureScalingMethod'

%%
ProximityLossModel
'ProximityLossModel'

%% Rac/Rdc
ACConductorLossRatio_OldMethod
ACConductorLossRatio_NewMethod
ACConductorLossUserRatio

'ACConductorLossRatio_OldMethod'
'ACConductorLossRatio_NewMethod'
'ACConductorLossUserRatio'
