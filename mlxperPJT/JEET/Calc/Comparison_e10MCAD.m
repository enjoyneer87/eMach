mcad(McadIndex).SetVariable("MessageDisplayState",1)


%% ref load V24
load('MatBy_e10_MCAD_refACLoss_v24_Irms460ang43.mat')
SpeedList=[1000:2000:15000];
figure(1)
plot(SpeedList,[Hybrid.DCConductorLoss_Armature_A{:}],"DisplayName",'DCLoss_{ActivePart}')
hold on
plot(SpeedList,[FullFEA.ACLossFullFEAEmagMCAD_Total{:}],'DisplayName','Diffusion')
% xline(TransitionSpeed)
plot(SpeedList,2.5*[Hybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','Hybrid')
% plot(SpeedList,[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','OPLab')
% plot(SpeedList,3*[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','3*OPLab')
legend

%% SC V24
load('MatBy_e10_MCAD_SCACLoss_v24_Irms920ang43.mat')
SpeedList=[1000:2000:15000];

figure(2)
plot(SpeedList,[Hybrid.DCConductorLoss_Armature_A{:}],"DisplayName",'DCLoss_{ActivePart}')
hold on
plot(SpeedList,[FullFEA.ACLossFullFEAEmagMCAD_Total{:}],'DisplayName','Diffusion')
% xline(TransitionSpeed)
plot(SpeedList,2.5*[Hybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','Hybrid_v24')
% plot(SpeedList,[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','OPLab')
% plot(SpeedList,3*[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','3*OPLab')
legend


%% ref V23
load('MatBy_e10_MCAD_refACLoss_Irms460ang43.mat')
SpeedList=[1000:1000:15000];
figure(1)
plot(SpeedList,[Hybrid.DCConductorLoss_Armature_A{:}],"DisplayName",'DCLoss_{ActivePart}')
hold on
plot(SpeedList,[FullFEA.ACLossFullFEAEmagMCAD_Total{:}],'DisplayName','Diffusion')
% xline(TransitionSpeed);
plot(SpeedList,2.5*[Hybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','Hybrid');
% plot(SpeedList,[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','OPLab')
% plot(SpeedList,3*[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','3*OPLab')
legend

%% SC V23
load('MatBy_e10_MCAD_SCACLoss_Irms920ang43.mat')
SpeedList=[1000:2000:15000];
figure(2)
plot(SpeedList,[Hybrid.DCConductorLoss_Armature_A{:}],"DisplayName",'DCLoss_{ActivePart}')
hold on
plot(SpeedList,[FullFEA.ACLossFullFEAEmagMCAD_Total{:}],'DisplayName','Diffusion')
% xline(TransitionSpeed);
plot(SpeedList,2.5*[Hybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','Hybrid_v23');
% plot(SpeedList,[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','OPLab')
% plot(SpeedList,3*[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','3*OPLab')
legend
