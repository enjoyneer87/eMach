

%% load V24
load('MatBy_e10_MCAD_refACLoss_v24_Irms460ang43.mat')
SpeedList=[1000:2000:15000];

plot(SpeedList,[Hybrid.DCConductorLoss_Armature_A{:}],"DisplayName",'DCLoss_{ActivePart}')
hold on
plot(SpeedList,[FullFEA.ACLossFullFEAEmagMCAD_Total{:}],'DisplayName','Diffusion')
xline(TransitionSpeed)
plot(SpeedList,[Hybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','Hybrid')
plot(SpeedList,[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','OPLab')
% plot(SpeedList,3*[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','3*OPLab')
legend

%%
load('MatBy_e10_MCAD_refACLoss_Irms460ang43.mat')
SpeedList=[1000:1000:15000];

plot(SpeedList,[Hybrid.DCConductorLoss_Armature_A{:}],"DisplayName",'DCLoss_{ActivePart}')
hold on
plot(SpeedList,[FullFEA.ACLossFullFEAEmagMCAD_Total{:}],'DisplayName','Diffusion')
% xline(TransitionSpeed);
plot(SpeedList,2.5*[Hybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','Hybrid');
% plot(SpeedList,[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','OPLab')
% plot(SpeedList,3*[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','3*OPLab')
legend

%% JMAG 

% Hybrid N Diffusion
% Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\deve10MQSplotAC.m

SpeedList=1000:1000:15000
ACLossJmag=...
[4355.6484417,
4496.78895445,
4702.58204942,
4985.34386333,
5333.31533767,
5734.53722212,
6158.92559051,
6620.03412326,
7132.27719291,
7681.37978144,
8240.95234081,
8805.84863344,
9404.4190626,
10026.804339,
10661.2973648];
Rph=0.007;
plot(SpeedList,ACLossJmag)

plot(SpeedList,ACLossJmag-3*Rph*460.^2)
hold on
%% 

%% SC - 1-2 turn
LossStudyResultTableObj=curStudyObj.GetResultTable
ResultDataStruct       = getJMagResultDatas(LossStudyResultTableObj,'voltage')

%% SC - 1-3 turn