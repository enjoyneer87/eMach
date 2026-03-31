mcad=callMCAD;
McadIndex=1;

refPath="F:\KDH\Thesis\JEET\e10\refModel\e10_UserRemesh.mot"
SCLPath=


%% setting 

SpeedList=[1000:1000:15000];
RMSCurrent    =460
PhaseAdvance  =43.33
StatorCurrentDemand_RMS_Lab=RMSCurrent;
PhaseAdvanceDemand_Lab     =PhaseAdvance;
%% MCAD FullFEA - Total Value
% Mesh Data
[~,TorquePointsPerCycle]      =mcad.GetVariable('TorquePointsPerCycle');
[~,StatorSlotMeshLength]      =mcad.GetVariable('StatorSlotMeshLength');
[~,AirgapMeshPoints_layers]   =mcad.GetVariable('AirgapMeshPoints_layers');
[~,AirgapMeshPoints_mesh]     =mcad.GetVariable('AirgapMeshPoints_mesh');

mcad.SetVariable('ProximityLossModel',2);
mcad.SetVariable('RMSCurrent',RMSCurrent);
mcad.SetVariable('PhaseAdvance',PhaseAdvance);

%% Full FEA - Calculation
for SpeedIndex=1:length(SpeedList)
mcad.SetVariable('ShaftSpeed',SpeedList(SpeedIndex));
mcad.DoMagneticCalculation()
% Load
% Conductor losses (DC + AC) calculated from FEA solution (on load) (active length only)
[~,ACLossFullFEAEmagMCAD_Total{SpeedIndex}]  =mcad.GetVariable('FEAProxLosses_OnLoad_Total');
[~,ACLossFullFEAEmagMCAD_Array{SpeedIndex}]  =mcad.GetVariable('FEAProxLosses_OnLoad_Array');
[~,FullFEAConductorSkinDepth{SpeedIndex}]           =mcad.GetVariable('ConductorSkinDepth');

% OC
% Conductor losses (DC + AC) calculated from FEA solution (open circuit)
[~,FEAProxLosses_OC_Total{SpeedIndex}]       =mcad.GetVariable('FEAProxLosses_OC_Total');
[~,FEAProxLosses_OC_Array{SpeedIndex}]       =mcad.GetVariable('FEAProxLosses_OC_Array');
% DC
[~,FullFEAConductor_DCLossEmagMCAD{SpeedIndex}]     =mcad.GetVariable('ConductorLoss');              % End part
[~,FullFEADCConductorLoss_Armature_A{SpeedIndex}]   =mcad.GetVariable('DCConductorLoss_Armature_A'); % ActivePart
end

plot(SpeedList,[ACLossFullFEAEmagMCAD_Total{:}])

%%
%[text] ## Hybrid - Calculation
% LAB
% Single FEA
% ACLossHighFrequencyScaling_Method-  The improved method introduces a further correction to Hybrid FEA AC losses when skin depth is significantly less than bundle height
% IMSingleLoadPoint_PBTorque- The power balance torque in the Single Load Point FEA case
% HybridModel_TotalLines -The total number of lines used in the hybrid loss model
% HybridModel_FEAFluxLinePoints- The number of points taken along each line in the hybrid loss model
% Defines the skew distrubution of the lines in the hybrid loss model
mcad.SetVariable('ProximityLossModel',1);

mcad.SetVariable('RMSCurrent',RMSCurrent);
mcad.SetVariable('PhaseAdvance',PhaseAdvance);

for SpeedIndex=1:length(SpeedList)
mcad.SetVariable('ShaftSpeed',SpeedList(SpeedIndex));
mcad.DoMagneticCalculation()
% Load
% hybridACLossModelStr=devCalcMCADHybridACLoss(mcad)
[~,ACConductorLoss_MagneticMethod_Total{SpeedIndex}]       =mcad.GetVariable('ACConductorLoss_MagneticMethod_Total');
[~,HybridConductorSkinDepth{SpeedIndex}]                   =mcad.GetVariable('ConductorSkinDepth');

% DC
[~,Conductor_DCLossEmagMCAD{SpeedIndex}]                   =mcad.GetVariable('ConductorLoss');
[~,DCConductorLoss_Armature_A{SpeedIndex}]                 =mcad.GetVariable('DCConductorLoss_Armature_A');
end

plot(SpeedList,[ACConductorLoss_MagneticMethod_Total{:}])

Hybrid=struct();
Hybrid.('ACConductorLoss_MagneticMethod_Total')            =ACConductorLoss_MagneticMethod_Total              ;                     
Hybrid.('ConductorSkinDepth')                              =HybridConductorSkinDepth       ;                   
Hybrid.('Conductor_DCLossEmagMCAD')                        =Conductor_DCLossEmagMCAD         ;                                 
Hybrid.('DCConductorLoss_Armature_A')                      =DCConductorLoss_Armature_A       ;                                   

varName2SaveList{end+1}='Hybrid';

%% MCAD OPLAB - Total Value
mcad.SetVariable('StatorCurrentDemand_RMS_Lab',StatorCurrentDemand_RMS_Lab);
mcad.SetVariable('PhaseAdvanceDemand_Lab'     ,PhaseAdvanceDemand_Lab);

for SpeedIndex=1:length(SpeedList)
mcad.SetVariable('SpeedDemand_MotorLAB',SpeedList(SpeedIndex));
mcad.CalculateOperatingPoint_Lab()
[~,ACLossHybridMCAD_LABOPPOint{SpeedIndex}]=mcad.GetVariable('LabOpPoint_StatorCopperLoss_AC');
end
plot(SpeedList,7*[ACLossHybridMCAD_LABOPPOint{:}])

OPLAB=struct();
OPLAB.('LabOpPoint_StatorCopperLoss_AC')            =ACLossHybridMCAD_LABOPPOint   ;                              
varName2SaveList{end+1}='OPLAB';


%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline"}
%---
