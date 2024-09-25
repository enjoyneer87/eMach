%% 선행 정보 추출
mcad=callMCAD;
McadIndex=1;
%% Save 
fullpath = mfilename("fullpath");
MatDir='Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET';

SpeedList=[1000:2000:15000];
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

% FullFEA 2Struct
FullFEA=struct();
FullFEA.('ACLossFullFEAEmagMCAD_Total')            =ACLossFullFEAEmagMCAD_Total              ;                     
FullFEA.('ACLossFullFEAEmagMCAD_Array')            =ACLossFullFEAEmagMCAD_Array              ;                     
FullFEA.('ConductorSkinDepth')                     =FullFEAConductorSkinDepth                       ;   
FullFEA.('FEAProxLosses_OC_Total')                 =FEAProxLosses_OC_Total                   ;           
FullFEA.('FEAProxLosses_OC_Array')                 =FEAProxLosses_OC_Array                   ;           
FullFEA.('Conductor_DCLossEmagMCAD')               =FullFEAConductor_DCLossEmagMCAD         ;                                 
FullFEA.('DCConductorLoss_Armature_A')             =FullFEADCConductorLoss_Armature_A       ;                                   
varName2SaveList{1}='FullFEA';

%% MCAD Hybrid - Total Value
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

%% PostCalculation
% conductorType='rectangular'
% [~, SimulationSmall.ShaftSpeed]    = mcad(McadIndex).GetVariable('ShaftSpeed');
% [~, SimulationSmall.pole]          = mcad(McadIndex).GetVariable('Pole_Number');
% [~, Copper_Width]                  = mcad(McadIndex).GetVariable('Copper_Width');
[~, Copper_Height]                 = mcad(McadIndex).GetVariable('Copper_Height');
% [~, Stator_Lam_Length]             = mcad(McadIndex).GetVariable('Stator_Lam_Length');
% % freqE=rpm2freqE(SimulationSmall.ShaftSpeed,SimulationSmall.pole/2)
% dimensions=[Copper_Width,Copper_Height,Stator_Lam_Length]
% % MCAD
% hybridACLossModelStr=devCalcMCADHybridACLoss(mcad)
% 
% CuboidModel          =hybridACLossModelStr.CuboidModel;
% Cuboid_Width         =unique(CuboidModel.Winding_Cuboid_Width);
% Cuboid_Height        =unique(CuboidModel.Winding_Cuboid_Height);
% % B
% for ConductorIndex=8:8
% % ConductorIndex=8
% ACLossCoductorWave=hybridACLossModelStr.OpDataGraph.Wave.ACLossCoductor
% PMCADACLoss=ACLossCoductorWave{ConductorIndex}.dataTable.GraphValue
% BWave=hybridACLossModelStr.OpDataGraph.Wave.BCoductor
% BfieldMCAD=BWave{ConductorIndex}
% BField=BfieldMCAD
% % dimensions=[Cuboid_Width,Cuboid_Height,lactive]
% [P_rect,P_1DInstant,P_1DrectG1,P1DrectG2,P_rect_nonGamma,P_rectMCAD1D,P_rec2DG1,P_rec2DG2]= calcHybridACLossWave(conductorType, dimensions, FreqE,BfieldMCAD)
% figure(ConductorIndex)
% plotXYarray([0:360/90:360],PMCADACLoss',P_rect1DData);
% meanGraphAC=mean(PMCADACLoss')
% hybridACLossModelStr.OutputDatabyMcad.PacLeft
% hold on
% plotXYarray([0:360/90:360],48*P_rectMCAD1D',P_rect1DData);
% a=1000*48*P_rectMCAD1D
% plotXYarray([0:360/90:360],48*P1DrectG2',P_rect1DData);
% % shifted_signalMCAD = circshift(P_rec2DJMAG, -20);
% % plotXYarray([0:3:360],shifted_signalMCAD,P_rect1DData);
% % plotXYarray([0:360/90:360],48*P_1DrectG1',P_rect1DData);
% % hold on
% % plotXYarray([0:360/90:360],48*P_rect',P_rect1DData);
% % plotXYarray([0:360/90:360],48*P_1DInstant',P_rect1DData);
% end


% 경로와 파일명을 분리
[currentFolder, MfileName, b] = fileparts(fullpath);
MfileName=strrep(MfileName,'dev','');
LoadInput = ['Irms',num2str(RMSCurrent),'ang',num2str(floor(PhaseAdvance))];
MatFilePath           = fullfile(MatDir,['MatBy_',MfileName,'_',LoadInput,'.mat']);
save(MatFilePath,varName2SaveList{:})



%% Check transition Speed
ConductorSkinDepth=[Hybrid.('ConductorSkinDepth'){:}];       
BoolResistanceLimit=ConductorSkinDepth>Copper_Height;
resistanceLimitSpeed=SpeedList(BoolResistanceLimit);
InductanceLimitSpeed=SpeedList(~BoolResistanceLimit);
Copper_Height=1.6


TransitionSpeed=resistanceLimitSpeed(end);
%% Plot
% SpeedList=[1000:1000:15000];
plot(SpeedList,[Hybrid.DCConductorLoss_Armature_A{:}],"DisplayName",'DCLoss_{ActivePart}')
hold on
plot(SpeedList,[FullFEA.ACLossFullFEAEmagMCAD_Total{:}],'DisplayName','Diffusion')
xline(TransitionSpeed)
plot(SpeedList,[Hybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','Hybrid')
plot(SpeedList,[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','OPLab')
plot(SpeedList,2.5*[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','3*OPLab')
legend
