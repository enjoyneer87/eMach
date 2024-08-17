

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
plot(SpeedList,[Hybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','Hybrid');
% plot(SpeedList,[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','OPLab')
% plot(SpeedList,3*[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','3*OPLab')
legend