%% 선행 정보 추출
McadIndex=1
conductorType='rectangular'
[~, SimulationSmall.ShaftSpeed]    = mcad(McadIndex).GetVariable('ShaftSpeed');
[~, SimulationSmall.pole]          = mcad(McadIndex).GetVariable('Pole_Number');
[~, Copper_Width]                  = mcad(McadIndex).GetVariable('Copper_Width');
[~, Copper_Height]                 = mcad(McadIndex).GetVariable('Copper_Height');
[~, Stator_Lam_Length]             = mcad(McadIndex).GetVariable('Stator_Lam_Length');
% freqE=rpm2freqE(SimulationSmall.ShaftSpeed,SimulationSmall.pole/2)
dimensions=[Copper_Width,Copper_Height,Stator_Lam_Length]
% MCAD
hybridACLossModelStr=devCalcMCADHybridACLoss(mcad)

CuboidModel          =hybridACLossModelStr.CuboidModel;
Cuboid_Width         =unique(CuboidModel.Winding_Cuboid_Width);
Cuboid_Height        =unique(CuboidModel.Winding_Cuboid_Height);
% B
for ConductorIndex=8:8
% ConductorIndex=8
ACLossCoductorWave=hybridACLossModelStr.OpDataGraph.Wave.ACLossCoductor
PMCADACLoss=ACLossCoductorWave{ConductorIndex}.dataTable.GraphValue
BWave=hybridACLossModelStr.OpDataGraph.Wave.BCoductor
BfieldMCAD=BWave{ConductorIndex}
BField=BfieldMCAD
% dimensions=[Cuboid_Width,Cuboid_Height,lactive]
[P_rect,P_1DInstant,P_1DrectG1,P1DrectG2,P_rect_nonGamma,P_rectMCAD1D,P_rec2DG1,P_rec2DG2]= calcHybridACLossWave(conductorType, dimensions, FreqE,BfieldMCAD)
figure(ConductorIndex)
plotXYarray([0:360/90:360],PMCADACLoss',P_rect1DData);
meanGraphAC=mean(PMCADACLoss')
hybridACLossModelStr.OutputDatabyMcad.PacLeft
hold on
plotXYarray([0:360/90:360],48*P_rectMCAD1D',P_rect1DData);
a=1000*48*P_rectMCAD1D
plotXYarray([0:360/90:360],48*P1DrectG2',P_rect1DData);
% shifted_signalMCAD = circshift(P_rec2DJMAG, -20);
% plotXYarray([0:3:360],shifted_signalMCAD,P_rect1DData);
% plotXYarray([0:360/90:360],48*P_1DrectG1',P_rect1DData);
% hold on
% plotXYarray([0:360/90:360],48*P_rect',P_rect1DData);
% plotXYarray([0:360/90:360],48*P_1DInstant',P_rect1DData);
end




%% jmag
Bfield4LayerLeft.Br         =L4r 
Bfield4LayerLeft.Bthetam    =L4t        
[P_rectJMAG,P_1DInstantJMAG,P_1DrectG1JMAG,P1DrectG2JMAG,P_rect_nonGammaJMAG,P_rectMCAD1DJMAG,P_rec2DJMAGG1,P_rec2DJMAGG2]= calcHybridACLossWave(conductorType, dimensions, FreqE,Bfield4LayerLeft)
conductorIndex=8
% [shifted_signalJMAG, phase_shift] = align_signals(P_rec2DJMAG, [0:3:360], PMCADACLoss', [0:360/90:360],-2, 'linear')
figure(conductorIndex)
hold on
shifted_signal2DJMAGG2   =48*circshift(P_rec2DJMAGG2, -21);
shifted_signal1DMCADJMAG =48*circshift(P_rectMCAD1DJMAG, -21);
shifted_signal2DJMAGG1   =48*circshift(P_rec2DJMAGG1, -21);


signal1DMCADJMAG =48*circshift(P_rectMCAD1DJMAG, 0);

plotXYarray([0:3:360],signal1DMCADJMAG,P_rect1DData);
mean(signal1DMCADJMAG)
hold on
plotXYarray([0:3:360],ACLossOnlyU2C5', P_rect1DData);  % Slot 1
mean(ACLossOnlyU2C5)

plotXYarray([0:3:360],ACLossOnlyU2C19', P_rect1DData);  % Slot 2
mean(ACLossOnlyU2C19)

% 
Hybrid=0.39
ACLoss=1.158


%% JMAG Hybrid AC

%% JMAG Diffusion AC - Total Value
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
10661.2973648]

plot(SpeedList,ACLossJmag-3*Rph*460.^2)
hold on

%% MCAD FullFEA - Total Value
SpeedList=[1000:1000:15000];
% Mesh Data
[~,TorquePointsPerCycle]=mcad.GetVariable('TorquePointsPerCycle');
[~,StatorSlotMeshLength]=mcad.GetVariable('StatorSlotMeshLength');
[~,AirgapMeshPoints_layers]=mcad.GetVariable('AirgapMeshPoints_layers');
[~,AirgapMeshPoints_mesh]=mcad.GetVariable('AirgapMeshPoints_mesh');

mcad.SetVariable('ProximityLossModel',2);
for SpeedIndex=1:length(SpeedList)
mcad.SetVariable('ShaftSpeed',SpeedList(SpeedIndex));
mcad.DoMagneticCalculation()

% LOad
% Conductor losses (DC + AC) calculated from FEA solution (on load) (active length only)
[~,ACLossFullFEAEmagMCAD_Total{SpeedIndex}]  =mcad.GetVariable('FEAProxLosses_OnLoad_Total');
[~,ACLossFullFEAEmagMCAD_Array{SpeedIndex}]  =mcad.GetVariable('FEAProxLosses_OnLoad_Array');
[~,ConductorSkinDepth{SpeedIndex}]=mcad.GetVariable('ConductorSkinDepth');

% OC
% Conductor losses (DC + AC) calculated from FEA solution (open circuit)
[~,FEAProxLosses_OC_Total{SpeedIndex}]       =mcad.GetVariable('FEAProxLosses_OC_Total');
[~,FEAProxLosses_OC_Array{SpeedIndex}]       =mcad.GetVariable('FEAProxLosses_OC_Array');
% DC
[~,FullFEA_Conductor_DCLossEmagMCAD{SpeedIndex}]=mcad.GetVariable('ConductorLoss');
[~,FullFEA_DCConductorLoss_Armature_A{SpeedIndex}]=mcad.GetVariable('DCConductorLoss_Armature_A');

end

plot(SpeedList,[ACLossFullFEAEmagMCAD{:}])
    

%% MCAD Hybrid - Total Value
% LAB
% Single FEA
% ACLossHighFrequencyScaling_Method-  The improved method introduces a further correction to Hybrid FEA AC losses when skin depth is significantly less than bundle height
% IMSingleLoadPoint_PBTorque- The power balance torque in the Single Load Point FEA case
% HybridModel_TotalLines -The total number of lines used in the hybrid loss model
% HybridModel_FEAFluxLinePoints- The number of points taken along each line in the hybrid loss model
% Defines the skew distrubution of the lines in the hybrid loss model
mcad.SetVariable('ProximityLossModel',1);

for SpeedIndex=1:length(SpeedList)
mcad.SetVariable('ShaftSpeed',SpeedList(SpeedIndex));
mcad.DoMagneticCalculation()
% Load
% hybridACLossModelStr=devCalcMCADHybridACLoss(mcad)
[~,ACConductorLoss_MagneticMethod_Total{SpeedIndex}]=mcad.GetVariable('ACConductorLoss_MagneticMethod_Total');
[~,ConductorSkinDepth{SpeedIndex}]=mcad.GetVariable('ConductorSkinDepth');

% DC
[~,Conductor_DCLossEmagMCAD{SpeedIndex}]=mcad.GetVariable('ConductorLoss');
[~,DCConductorLoss_Armature_A{SpeedIndex}]=mcad.GetVariable('DCConductorLoss_Armature_A');
end
plot(SpeedList,[ACLossHybridEMagMCAD{:}])
    
%% MCAD OPLAB - Total Value
for SpeedIndex=1:length(SpeedList)
mcad.SetVariable('SpeedDemand_MotorLAB',SpeedList(SpeedIndex));
mcad.CalculateOperatingPoint_Lab()
[~,ACLossHybridMCAD_LABOPPOint{SpeedIndex}]=mcad.GetVariable('LabOpPoint_StatorCopperLoss_AC');
end
plot(SpeedList,7*[ACLossHybridMCAD_LABOPPOint{:}])
