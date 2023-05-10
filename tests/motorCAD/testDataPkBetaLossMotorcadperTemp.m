%% MotorCADData object make temp=65
HDEVMotorCADTemp65=MotorcadData(12);
HDEVMotorCADTemp65.motorcadMotPath='Z:\Thesis\Optislang_Motorcad\Validation'
HDEVMotorCADTemp65.motocadLabPath=strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
HDEVMotorCADTemp65.proj_path=HDEVMotorCADTemp65.motorcadMotPath;
HDEVMotorCADTemp65.file_path=HDEVMotorCADTemp65.proj_path;
HDEVMotorCADTemp65.matfileFindList=what(HDEVMotorCADTemp65.motocadLabPath);
HDEVMotorCADTemp65.file_name='HDEV_Model2Temp115';
global phasemesh
global currentmesh

%% Same as  Raw PsiModel_Lab Current Vector 
HDEVdata=DataPkBetaMap(HDEVMotorCADTemp65.p);
%%currentVec
NcurrentVec=5
currentMax=1000;
currentVec=[0:currentMax/(NcurrentVec):currentMax]'
phaseMax=90;
NphaseVec=5
phaseVec=[0:phaseMax/(NphaseVec-1):phaseMax];
HDEVdata.phaseVec=phaseVec;
HDEVdata.currentVec=currentVec;

%% mesh for FE Loss coeffi data 
PmsmFem.NumPolePairs = HDEVdata.p/2;
currentmesh = repmat(HDEVdata.currentVec,1,length(phaseVec))
% size(currentmesh)
phasemesh = repmat(HDEVdata.phaseVec,length(currentmesh),1)


%% LabMat Import - ref compMatFile
HDEVMotorCADTemp65.proj_path=HDEVMotorCADTemp65.motorcadMotPath;
HDEVMotorCADTemp65.file_path=HDEVMotorCADTemp65.proj_path;

HDEVMotorCADTemp65.motocadLabPath=strcat('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2','\Lab\');
HDEVMotorCADTemp65.matfileFindList=what(HDEVMotorCADTemp65.motocadLabPath);

HDEVMotorCADTemp65.matfileFindList.mat
i=9
HDEVdata.MotorcadMat=load(HDEVMotorCADTemp65.matfileFindList.mat{i})
HDEVdata=HDEVdata.compMatiFilePsi()
HDEVdata=HDEVdata.compMatFileLoss()


HDEVdata.LossMap.HysCoeff.CoeffValue;

%% Plot Mat loss from ? (High Fidel)
tempLoss=inputobj.LossParameters_MotorLAB.RawLossMap;
HDEVMotorCADTemp65=HDEVMotorCADTemp65.exportRawLossMap()
figure(1)
ax=gca;
CoeffIndex=2
zName=HDEVdata.LossMap.HysCoeff.CoeffName(CoeffIndex);
zName=zName{1};
zUnit=HDEVdata.LossMap.HysCoeff.CoeffUnit(CoeffIndex);
zUnit=zUnit{1};


surf(HDEVdata.MotorcadMat.Phase_Advance(1,:), HDEVdata.MotorcadMat.Stator_Current_Line_Peak(:,1),HDEVdata.LossMap.HysCoeff.CoeffValue.(zName),'DisplayName',strrep(strcat(zName,'@65deg'),'_',' '));
ax.ZLabel.String=zUnit;
ax.Parent.Name=zName;
formatterSCI_IpkBeta;
legend('Location', 'best');
hold on
surf(GammaVec,IsVec,1.5*tempLoss.FeHysLossArray_MotorLAB);

hold on
% scatter3(matData.Phase_Advance,matData.Stator_Current_Line_Peak,flux1D,'red')
figure(2)
ax=gca;
CoeffIndex=2;
zName=HDEVdata.LossMap.EddyCoeff.CoeffName(CoeffIndex);
zName=zName{1};
zUnit=HDEVdata.LossMap.EddyCoeff.CoeffUnit(CoeffIndex);
zUnit=zUnit{1};


surf(HDEVdata.MotorcadMat.Phase_Advance(1,:), HDEVdata.MotorcadMat.Stator_Current_Line_Peak(:,1),HDEVdata.LossMap.EddyCoeff.CoeffValue.(zName),'DisplayName',strrep(strcat(zName,'@65deg'),'_',' '));
ax.ZLabel.String=zUnit;
ax.Parent.Name=zName;
formatterSCI_IpkBeta;
legend('Location', 'best');

hold on
%% SettingMotorCADwithInterface
settingMotorCADwithInterface

%% From LossMap .Mot 
IsVec=inputobj.LossParameters_MotorLAB.RawLossMap.LossModel_Is_Lab(:,1)
GammaVec=inputobj.LossParameters_MotorLAB.RawLossMap.LossModel_Gamma_Lab(1,:);


%% Iron Loss 검증 (LossMap PostComputation in Matlab <-> MotorCAD Lab Operating Point )

IsVec(3)
GammaVec(3)

HysLoss=f*inputobj.LossParameters_MotorLAB.RawLossMap.FeHysLossArray_MotorLAB(3,3)
EddyLoss=f^2*inputobj.LossParameters_MotorLAB.RawLossMap.FeEddyLossArray_MotorLAB(3,3)
IronLoss=1.5*(HysLoss+EddyLoss)

%% AC Loss 검증
ModelParameters_MotorLAB.TwindingCalc_MotorLAB =115;
% Set MotorParameters_MotorLAb
for fieldIndex=1:length(names_ModelParameters_MotorLAB)
    mcad.SetVariable(names_ModelParameters_MotorLAB{fieldIndex},ModelParameters_MotorLAB.(names_ModelParameters_MotorLAB{fieldIndex}));
end
mcad.CalculateOperatingPoint_Lab()
% Import Result
LabOpIndex=1;
LabOpFieldsName=fieldnames(LabOp_struct(LabOpIndex));
for fieldIndex=1:length(fieldnames(LabOp_struct(LabOpIndex)))
    [success,charTypeData]=mcad.GetVariable(LabOpFieldsName{fieldIndex});
    LabOp_struct(LabOpIndex).(LabOpFieldsName{fieldIndex}) =  charTypeData;
end
LabOp_struct(LabOpIndex).LabOpPoint_StatorTemp_Average
LabOp_struct(LabOpIndex).LabOpPoint_StatorCopperLoss_AC
LabOp_struct(LabOpIndex).LabOpPoint_StatorCopperLoss_DC


% 2 Set SimulationParameter_MotorLab

% SimulationParameter_MotorLab.SpeedDemand_MotorLAB=2000;
% for fieldIndex=1:length(namesSimulationParameter_MotorLab)
%     mcad.SetVariable(namesSimulationParameter_MotorLab{fieldIndex},SimulationParameter_MotorLab.(namesSimulationParameter_MotorLab{fieldIndex}));
% end

ModelParameters_MotorLAB.TwindingCalc_MotorLAB =65;

% Set MotorParameters_MotorLAb
for fieldIndex=1:length(names_ModelParameters_MotorLAB)
    mcad.SetVariable(names_ModelParameters_MotorLAB{fieldIndex},ModelParameters_MotorLAB.(names_ModelParameters_MotorLAB{fieldIndex}));
end
mcad.CalculateOperatingPoint_Lab()

% 2 Import Result
LabOpIndex=2;
LabOp_struct(2)
LabOpFieldsName=fieldnames(LabOp_struct(LabOpIndex));
for fieldIndex=1:length(fieldnames(LabOp_struct(LabOpIndex)))
    [success,charTypeData]=mcad.GetVariable(LabOpFieldsName{fieldIndex});
    LabOp_struct(LabOpIndex).(LabOpFieldsName{fieldIndex}) =  charTypeData;
end


LabOp_struct(LabOpIndex).LabOpPoint_StatorTemp_Average
LabOp_struct(LabOpIndex).LabOpPoint_StatorCopperLoss_AC
LabOp_struct(LabOpIndex).LabOpPoint_StatorCopperLoss_DC

% Comparison
LabOp_struct(1).LabOpPoint_StatorCopperLoss_AC
LabOp_struct(2).LabOpPoint_StatorCopperLoss_AC

% ModelParameters_MotorLAB.TwindingCalc_MotorLAB=115
% ModelParameters_MotorLAB.WindingAlpha_MotorLAB=0.003862
% 

%% AC Loss Temperature and speed Dependencies
TempScailedAC=LabOp_struct(1).LabOpPoint_StatorCopperLoss_AC*((SimulationParameter_MotorLab.SpeedDemand_MotorLAB/ModelParameters_MotorLAB.FEALossMap_RefSpeed_Lab)...
    ^LossParameters_MotorLAB_struct.AcLossFreq_MotorLAB)/((1+ModelParameters_MotorLAB.WindingAlpha_MotorLAB*(ModelParameters_MotorLAB.TwindingCalc_MotorLAB-20))/...
    (1+ModelParameters_MotorLAB.WindingAlpha_MotorLAB*(ThermalParameters_MotorLAB.WindingTemp_ACLoss_Ref_Lab-20)))^Losses_At_RPM_Ref.StatorCopperFreqCompTempExponent

% TempScailedAC=LabOp_struct(1).LabOpPoint_StatorCopperLoss_AC*(1/(1+ModelParameters_MotorLAB.WindingAlpha_MotorLAB*(ModelParameters_MotorLAB.TwindingCalc_MotorLAB-ThermalParameters_MotorLAB.WindingTemp_ACLoss_Ref_Lab))^Losses_At_RPM_Ref.StatorCopperFreqCompTempExponent)


ratio_speed=LabOp_struct(2).LabOpPoint_StatorCopperLoss_AC/LabOp_struct(1).LabOpPoint_StatorCopperLoss_AC

LabOp_struct(1).LabOpPoint_StatorCopperLoss_DC
LabOp_struct(2).LabOpPoint_StatorCopperLoss_DC

RacRdcFromValue=LabOp_struct(1).LabOpPoint_StatorCopperLoss_DC/LabOp_struct(1).LabOpPoint_StatorCopperLoss_AC

% 
WindingTemp_ACLoss_Ref_Lab
RacRdc_MotorLAB=LossParameters_MotorLAB_struct.RacRdc_MotorLAB;
AcLossFreq_MotorLAB=LossParameters_MotorLAB_struct.AcLossFreq_MotorLAB;
MagLoss=BuildFactor_MagnetLoss*MagLossMap*(SpeedDemand_MotorLAB/refSpeed)^SpeedCoeff_MagLossMotorLAB;


%% Magnet Loss  검증 (LossMap PostComputation in Matlab <-> MotorCAD Lab Operating Point )

% import LossMap
MagLossMap=inputobj.LossParameters_MotorLAB.RawLossMap.MagLossArray_MotorLAB(3,3)
refSpeed=inputobj.LossParameters_MotorLAB.RawLossMap.FEALossMap_RefSpeed_Lab;
SpeedCoeff_MagLossMotorLAB=LossParameters_MotorLAB_struct.MagLossCoeff_MotorLAB;
BuildFactor_MagnetLoss=Magnetics.MagnetLossBuildFactor;
% Post Computation Magnet Loss with Factor and Coefficient
MagLoss=BuildFactor_MagnetLoss*MagLossMap*(SpeedDemand_MotorLAB/refSpeed)^SpeedCoeff_MagLossMotorLAB;
% import Op Loss
LabOp_struct.LabOpPoint_MagnetLoss;

%% Magnet Loss Temperater Dependencies 
ModelParameters_MotorLAB.TmagnetCalc_MotorLAB=80;
% Set MotorParameters_MotorLAb
for fieldIndex=1:length(names_ModelParameters_MotorLAB)
    mcad.SetVariable(names_ModelParameters_MotorLAB{fieldIndex},ModelParameters_MotorLAB.(names_ModelParameters_MotorLAB{fieldIndex}));
end


mcad.CalculateOperatingPoint_Lab()

% Import Result
LabOpFieldsName=fieldnames(LabOp_struct(3));
for fieldIndex=1:length(fieldnames(LabOp_struct(3)))
    [success,charTypeData]=mcad.GetVariable(LabOpFieldsName{fieldIndex});
    LabOp_struct(4).(LabOpFieldsName{fieldIndex}) =  charTypeData;
end

% No difference
LabOp_struct(1).LabOpPoint_MagnetLoss
LabOp_struct(2).LabOpPoint_MagnetLoss



%% Lab Operating Point


%%
%%
refTempMotorcad = refTempMotorcad.rawPsiDataPost();
