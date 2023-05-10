







%% Structure Field 로 변경할것   exportRawLossMap  참조
% mcad = actxserver('MotorCAD.AppAutomation');


% StatorWindingTemperatureAtWhichPcuInput


%% ModelParameters_MotorLAB
ModelParameters_MotorLAB=struct();
% RotorWindingTemp_Ref_Lab
% RotorWindingTemp_Calc_Lab
ModelParameters_MotorLAB.FEALossMap_RefSpeed_Lab                             =[];
%
ModelParameters_MotorLAB.TmagnetCalc_MotorLAB                                = []
ModelParameters_MotorLAB.TwindingCalc_MotorLAB                               = [] 
ModelParameters_MotorLAB.LabOpPoint_CustomThermalLimitsTemperatures          = []                      
ModelParameters_MotorLAB.RotorWindingTempCoeffResistivity_Lab                = []                
ModelParameters_MotorLAB.ResultsPath_MotorLAB                                = []
ModelParameters_MotorLAB.WindingAlpha_MotorLAB                               = [] 
%                                
ModelParameters_MotorLAB.WindingTemp_ACLoss_Ref_Lab                          = []      
%
ModelParameters_MotorLAB.ModulationIndex_MotorLAB                            =[];                            
%
ModelParameters_MotorLAB.LabModel_ACLoss_Method                              =[];                          
ModelParameters_MotorLAB.LabModel_ACLoss_StatorCurrent_Peak                  =[];                                      
ModelParameters_MotorLAB.LabModel_ACLoss_StatorCurrent_RMS                   =[];                                     
ModelParameters_MotorLAB.LabModel_ACLoss_RotorCurrent                        =[];                                
ModelParameters_MotorLAB.LabModel_MagnetLoss_Date                            =[];                            
ModelParameters_MotorLAB.LabModel_MagnetLoss_Method                          =[];                              
ModelParameters_MotorLAB.LabModel_MagnetLoss_StatorCurrent_Peak              =[];                                          
ModelParameters_MotorLAB.LabModel_MagnetLoss_StatorCurrent_RMS               =[];                                         
ModelParameters_MotorLAB.LossModel_AC_Lab                                    =[];
% Import;
names_ModelParameters_MotorLAB = {}; % LabOpPoint 문자열이 포함된 변수 이름들을 저장할 셀 배열


% Import Result
names_ModelParameters_MotorLAB=fieldnames(ModelParameters_MotorLAB);
for fieldIndex=1:length(names_ModelParameters_MotorLAB)
    [success,charTypeData]=mcad.GetVariable(names_ModelParameters_MotorLAB{fieldIndex});
    ModelParameters_MotorLAB.(names_ModelParameters_MotorLAB{fieldIndex}) =  charTypeData;
end

% Set ModelParameters_MotorLAB
for fieldIndex=1:length(names_ModelParameters_MotorLAB)
    mcad.SetVariable(names_ModelParameters_MotorLAB{fieldIndex},ModelParameters_MotorLAB.(names_ModelParameters_MotorLAB{fieldIndex}));
end

%% LossParameters_MotorLAB
LossParameters_MotorLAB_struct = struct(); % 구조체 생성


LossParameters_MotorLAB_struct.BuildLossModel_MotorLAB                             =[];                          
LossParameters_MotorLAB_struct.LossModel_Lab                                       =[];                                                                      

LossParameters_MotorLAB_struct.IronLossCalc_Lab                                    =[];                  
LossParameters_MotorLAB_struct.IronLossCalc_SPEED_Lab                              =[];                        
LossParameters_MotorLAB_struct.BPM_IronLossSpeedCalc_Lab                           =[];                           
LossParameters_MotorLAB_struct.CalcTypeCuLoss_MotorLAB                             =[];                         
LossParameters_MotorLAB_struct.MagnetLossCalc_Lab                                  =[];                    
LossParameters_MotorLAB_struct.MagnetLossCalc_SPEED_Lab                            =[];                          
LossParameters_MotorLAB_struct.Resistance_MotorLAB                                 =[];                     
LossParameters_MotorLAB_struct.Ah_MotorLAB                                         =[];             
LossParameters_MotorLAB_struct.Ae_MotorLAB                                         =[];             
LossParameters_MotorLAB_struct.Bh_MotorLAB                                         =[];             
LossParameters_MotorLAB_struct.Be_MotorLAB                                         =[];             
LossParameters_MotorLAB_struct.n2ac_MotorLAB                                       =[];                                                                  
% Magnet                                            =[];          
LossParameters_MotorLAB_struct.Wmag_MotorLAB                                       =[];               
LossParameters_MotorLAB_struct.Imag_MotorLAB                                       =[];               
LossParameters_MotorLAB_struct.Nmag_MotorLAB                                       =[];               
LossParameters_MotorLAB_struct.WmagOC_MotorLAB                                     =[];                 
LossParameters_MotorLAB_struct.MagLossCoeff_MotorLAB                               =[];                                                                              
%                                                   =[];   
LossParameters_MotorLAB_struct.RotorlronEddyLossExponent_Lab                       =[];                               
%                                                   =[];   
LossParameters_MotorLAB_struct.AcLossFreq_MotorLAB                                 =[];                     
LossParameters_MotorLAB_struct.RacRdc_MotorLAB                                     =[];                              
LossParameters_MotorLAB_struct.ACConductorLossSplit_Lab                            =[];                          
LossParameters_MotorLAB_struct.ACLossSpeedScalingMethod_Lab                        =[];                              
LossParameters_MotorLAB_struct.ACLossGeneratorMethod_Lab                           =[];                                                                                 
%Iron                                               =[];       
LossParameters_MotorLAB_struct.FeHysLossArray_MotorLAB                             =[];                         
LossParameters_MotorLAB_struct.FeHysLossArray_Stator_Lab                           =[];                           
LossParameters_MotorLAB_struct.FeHysLossArray_Rotor_Lab                            =[];                          
LossParameters_MotorLAB_struct.FeEddyLossArray_MotorLAB                            =[];                          
LossParameters_MotorLAB_struct.FeEddyLossArray_Stator_Lab                          =[];                            
LossParameters_MotorLAB_struct.FeEddyLossArray_Rotor_Lab                           =[];                           
LossParameters_MotorLAB_struct.FeLossRotorEd_MotorLAB                              =[];                        
LossParameters_MotorLAB_struct.FeLossBackIronEd_MotorLAB                           =[];                           
LossParameters_MotorLAB_struct.FeLossToothEd_MotorLAB                              =[];                        
LossParameters_MotorLAB_struct.FeLossRotorHy_MotorLAB                              =[];                        
LossParameters_MotorLAB_struct.FeLossBacklronHy_MotorLAB                           =[];                           
LossParameters_MotorLAB_struct.FeLossToothHy_MotorLAB                              =[];                        
LossParameters_MotorLAB_struct.FeLossRotorPoleHy_MotorLAB                          =[];                            
LossParameters_MotorLAB_struct.FeLossRotorPoleEd_MotorLAB                          =[];                                                                                    
%Magnet                                             =[];          
LossParameters_MotorLAB_struct.MagLossArray_MotorLAB                               =[];                       
LossParameters_MotorLAB_struct.ACConductorLossProportion_Lab                       =[];     

% set LossParameters_MotorLAB
variable_names = who; % 작업공간의 변수 이름들 가져오기
LossParameters_MotorLAB_names = {}; % 

% for i = 1:numel(variable_names)
%     if contains(variable_names{i}, 'MotorLAB') % 변수 이름 검사
%         LossParameters_MotorLAB_names{end+1} = variable_names{i}; % 해당 변수 이름 저장
%     end
% end
% 
% 
% for i = 1:numel(LossParameters_MotorLAB_names)
%     LossParameters_MotorLAB_struct.(LossParameters_MotorLAB_names{i}) = eval(LossParameters_MotorLAB_names{i}); % 구조체에 필드 추가
% end

% % Import Result
LossParametersFieldsName=fieldnames(LossParameters_MotorLAB_struct);
for fieldIndex=1:length(fieldnames(LossParameters_MotorLAB_struct))
    [success,charTypeData]=mcad.GetVariable(LossParametersFieldsName{fieldIndex});
    LossParameters_MotorLAB_struct.(LossParametersFieldsName{fieldIndex}) =  charTypeData;
end


%% SaturationMap                                                        
SaturationMap_CalculationStatus                                                        
SaturationMap_ExportToCSV                                                        
%% ThermalParameters_MotorLAB
ThermalParameters_MotorLAB=struct();
ThermalParameters_MotorLAB.BrTempCoeff_MotorLAB                                = [];                                
ThermalParameters_MotorLAB.RotorTemperatureTolerance_Lab                       = [];                     
ThermalParameters_MotorLAB.Tmag_MotorLAB                                       = [];     
ThermalParameters_MotorLAB.WindingTemp_ACLoss_Ref_Lab                          = [];                  
ThermalParameters_MotorLAB.Twdg_MotorLAB                                       = [];    
ThermalParameters_MotorLAB.MaxMagnet_MotorLAB                                  = [];          
ThermalParameters_MotorLAB.MaxWindTemp_MotorLAB                                = [];

% Import Result
names_ThermalParameters_MotorLAB=fieldnames(ThermalParameters_MotorLAB);
for fieldIndex=1:length(names_ThermalParameters_MotorLAB)
    [success,charTypeData]=mcad.GetVariable(names_ThermalParameters_MotorLAB{fieldIndex});
    ThermalParameters_MotorLAB.(names_ThermalParameters_MotorLAB{fieldIndex}) =  charTypeData;
end

% Set ThermalParameters_MotorLAB
for fieldIndex=1:length(names_ThermalParameters_MotorLAB)
    mcad.SetVariable(names_ThermalParameters_MotorLAB{fieldIndex},ThermalParameters_MotorLAB.(names_ThermalParameters_MotorLAB{fieldIndex}));
end

%% Losses_At_RPM_Ref
Losses_At_RPM_Ref=struct()
Losses_At_RPM_Ref.StatorWindingTemperatureAtWhichPcuInput             = [];      
Losses_At_RPM_Ref.RotorWindingTemperatureAtWhichPcuInput              = [];     
Losses_At_RPM_Ref.StatorCopperFreqCompTempExponent                    = 0.7

% Import Result
names_Losses_At_RPM_Ref=fieldnames(Losses_At_RPM_Ref);
for fieldIndex=1:length(names_Losses_At_RPM_Ref)
    [success,charTypeData]=mcad.GetVariable(names_Losses_At_RPM_Ref{fieldIndex});
    Losses_At_RPM_Ref.(names_Losses_At_RPM_Ref{fieldIndex}) =  charTypeData;
end

% Set ModelParameters_MotorLAB
for fieldIndex=1:length(names_Losses_At_RPM_Ref)
    mcad.SetVariable(names_Losses_At_RPM_Ref{fieldIndex},Losses_At_RPM_Ref.(names_Losses_At_RPM_Ref{fieldIndex}));
end

%% Magnetics
Magnetics=struct()
Magnetics.Airgap_Temperature                                  =[];
Magnetics.Bearing_Temperature_F                               =[];  
Magnetics.Magnet_Temperature                                  =[];
Magnetics.Bearing_Temperature_R                               =[];  
Magnetics.Shaft_Temperature                                   =[];
Magnetics.ArmatureConductor_Temperature                       =[];          
Magnetics.DCBusVoltage                                        =[];              
Magnetics.ModulationIndex_MotorLAB                            =[];                                                                 
% Build Factor                                      =[]          ;      
Magnetics.IronLossBuildFactorDefinition                       =[];                               
Magnetics.StatorIronLossBuildFactor                           =[];                            
Magnetics.RotorIronLossBuildFactor                            =[];                          
Magnetics.HysteresisLossBuildFactor                           =[];                           
Magnetics.EddyLossBuildFactor                                 =[];                     
Magnetics.MagnetLossBuildFactor                               =[];                                                               
Magnetics.BMax_StatorBackIron_Static                          =[];                            
Magnetics.BMax_StatorBackIron_Static                          =[];                                                                            
% Ac loss                                           =[]          ; 
Magnetics.ACConductorLoss_MagneticMethod                      =[];                                
Magnetics.ACConductorLoss_MagneticMethod_L                    =[];                                  
Magnetics.ACConductorLoss_MagneticMethod_R                    =[];                                  
Magnetics.ACConductorLoss_FluxDensity                         =[];                             
Magnetics.ACConductorLoss_FluxDensity_L                       =[];                               
Magnetics.ACConductorLoss_FluxDensity_R                       =[];                               
Magnetics.ACConductorLossProportion                           =[];                           
Magnetics.ACConductorLossRatio_OldMethod                      =[];                                
Magnetics.ACConductorLossRatio_NewMethod                      =[];                                
Magnetics.ACConductorLossUserValues                           =[];                           
Magnetics.ACConductorLossUserRatio                            =[];                          
Magnetics.ACConductorLoss_MagneticMethod_Total                =[];                                      
Magnetics.ACConductorLoss_MagneticMethod_Total_L              =[];                                        
Magnetics.ACConductorLoss_MagneticMethod_Total_R              =[];     
% Import;
Magnetics_names = {}; % 

% Import Result
Magnetics_names=fieldnames(Magnetics);
for fieldIndex=1:length(Magnetics_names)
    [success,charTypeData]=mcad.GetVariable(Magnetics_names{fieldIndex});
    Magnetics.(Magnetics_names{fieldIndex}) =  charTypeData;
end

% Set Magnetics
for fieldIndex=1:length(Magnetics_names)
    mcad.SetVariable(Magnetics_names{fieldIndex},Magnetics.(Magnetics_names{fieldIndex}));
end


%% SimulationParameter_MotorLab
SimulationParameter_MotorLab=struct()
SimulationParameter_MotorLab.DCCurrentLimit_Lab                      =    []      
SimulationParameter_MotorLab.MaxDCCurrent_Lab                        =    []    
SimulationParameter_MotorLab.ControlStrat_MotorLAB                   =    []         
%                            =    []
SimulationParameter_MotorLab.NumControlStrategyPoints_Lab            =    []                
SimulationParameter_MotorLab.ControlStrat_Speed_Lab                  =    []          
SimulationParameter_MotorLab.ControlStrat_PhaseAdvance_Lab           =    []                 
%                            =    []
SimulationParameter_MotorLab.ThermalEnvelopeSensitivity_Lab          =    []                  
SimulationParameter_MotorLab.StatorTempDemand_Lab                    =    []        
SimulationParameter_MotorLab.RotorTempDemand_Lab                     =    []       
SimulationParameter_MotorLab.SpeedDemand_MotorLAB                    =    1000        
SimulationParameter_MotorLab.TorqueDemand_MotorLAB                   =    []         
SimulationParameter_MotorLab.PhaseAdvanceDemand_Lab                  =    45          
SimulationParameter_MotorLab.StatorCurrentDemand_Lab                 =    400           
SimulationParameter_MotorLab.StatorCurrentDemand_RMS_Lab             =    []               
SimulationParameter_MotorLab.RotorCurrentDemand_Lab                  =    []          
SimulationParameter_MotorLab.MaxNumAltStartPoints_Lab                =    []            
SimulationParameter_MotorLab.SlipDemand_Lab                          =    []  
SimulationParameter_MotorLab.OperatingMode_Lab                       =    []     
SimulationParameter_MotorLab.OpPointSpec_MotorLAB                    =3 % 0 Torque 1: Maximum Current 2: Maximum Temperature 3: Current
SimulationParameter_MotorLab.LabThermalCoupling                     =[]
SimulationParameter_MotorLab.LabMagneticCoupling                    =[]

% Import Result
namesSimulationParameter_MotorLab=fieldnames(SimulationParameter_MotorLab);
for fieldIndex=1:length(namesSimulationParameter_MotorLab)
    [success,charTypeData]=mcad.GetVariable(namesSimulationParameter_MotorLab{fieldIndex});
    SimulationParameter_MotorLab.(namesSimulationParameter_MotorLab{fieldIndex}) =  charTypeData;
end

% Set 
for fieldIndex=1:length(namesSimulationParameter_MotorLab)
    mcad.SetVariable(namesSimulationParameter_MotorLab{fieldIndex},SimulationParameter_MotorLab.(namesSimulationParameter_MotorLab{fieldIndex}));
end



%% OperatingPointParameters_Lab
LabOpPoint_ShaftSpeed                    =[]    
LabOpPoint_ShaftTorque                   =[]     
LabOpPoint_ShaftPower                    =[]    
LabOpPoint_Efficiency                    =[]    
LabOpPoint_PhaseCurrent_D_Peak           =[]             
LabOpPoint_PhaseCurrent_Q_Peak           =[]             
LabOpPoint_PhaseCurrent_D_RMS            =[]            
LabOpPoint_PhaseCurrent_Q_RMS            =[]            
LabOpPoint_PhaseAdvance                  =[]      
LabOpPoint_Slip                          =[]
LabOpPoint_Frequency                     =[]   
LabOpPoint_StatorCurrent_Phase_Peak      =[]                  
LabOpPoint_StatorCurrent_Phase_RMS       =[]                 
LabOpPoint_StatorCurrent_Line_Peak       =[]                 
LabOpPoint_StatorCurrent_Line_RMS        =[]                
LabOpPoint_TerminalCurrent               =[]         
LabOpPoint_RotorCurrent_Peak             =[]           
LabOpPoint_RotorCurrent_RMS              =[]          
LabOpPoint_RotorCurrent_Ref_Peak         =[]               
LabOpPoint_RotorCurrent_Ref_RMS          =[]              
LabOpPoint_EndringCurrent_Peak           =[]             
LabOpPoint_EndringCurrent_RMS            =[]            
LabOpPoint_RotorCurrent_DC               =[]         
LabOpPoint_MagnetizingCurrent_Peak       =[]                 
LabOpPoint_MagnetizingCurrent_RMS        =[]                
LabOpPoint_TotalLoss                     =[]   
LabOpPoint_StatorCopperLoss              =[]          
LabOpPoint_StatorCopperLoss_AC           =[]             
LabOpPoint_StatorCopperLoss_DC           =[]
%
LabOpPoint_IronLoss                      =[]                        
LabOpPoint_IronLossStator                =[]                              
LabOpPoint_IronLossRotor                 =[]                             
LabOpPoint_IronLossHysteresis            =[]                                  
LabOpPoint_IronLossEddy                  =[]                            
LabOpPoint_StatorBacklronLoss            =[]                                  
LabOpPoint_StatorToothLoss               =[]                               
LabOpPoint_RotorBacklronLoss             =[]                                 
LabOpPoint_RotorMagnetPoleLoss           =[]                                   
LabOpPoint_RotorToothLoss                =[]         
%                        =[]
LabOpPoint_MagnetLoss                    =[]                          
LabOpPoint_SleeveLoss                    =[]                          
LabOpPoint_BandingLoss                   =[]                           
LabOpPoint_MechanicalLoss                =[]                              
LabOpPoint_WindageLoss                   =[]                           
LabOpPoint_FrictionLoss                  =[];                            
LabOpPoint_FrictionLoss_F                =[]                              
LabOpPoint_FrictionLoss_R                =[]                              
LabOpPoint_StrayLoadLoss                 =[]            
%                        =[]
LabOpPoint_EmagneticPower                =[]                              
LabOpPoint_EmagneticTorque               =[]                               
LabOpPoint_MagnetTorque                  =[]                            
LabOpPoint_ReluctanceTorque              =[]                                
LabOpPoint_TerminalPower                 =[]                             
LabOpPoint_PowerFactor                   =[]                           
LabOpPoint_PowerFactorBalance            =[]                                  
%                        =[]
LabOpPoint_Voltage_Phase_Peak            =[]           
LabOpPoint_Voltage_Phase_RMS             =[]          
LabOpPoint_Voltage_Line_Peak             =[]          
LabOpPoint_Voltage_Line_RMS              =[]         
LabOpPoint_PhaseVoltage_D_Peak           =[]            
LabOpPoint_PhaseVoltage_Q_Peak           =[]            
LabOpPoint_PhaseVoltage_D_RMS            =[]           
LabOpPoint_PhaseVoltage_Q_RMS            =[]           
LabOpPoint_FluxLinkage_D                 =[]      
LabOpPoint_FluxLinkage_Q                 =[]      
LabOpPoint_FluxLinkage_Magnet            =[]           
LabOpPoint_Inductance_D                  =[]     
LabOpPoint_Inductance_Q                  =[]     
LabOpPoint_StatorLeakageReactance        =[]               
LabOpPoint_RotorLeakageReactance_Ref     =[]                  
LabOpPoint_MagnetizingReactance          =[]             
LabOpPoint_Magnetizinglnductance         =[]              
LabOpPoint_StatorTemp_Average            =[]           
LabOpPoint_StatorTemp_Max                =[]       
LabOpPoint_AirgapTemp                    =[]   
LabOpPoint_BearingTemp_Front             =[]          
LabOpPoint_BearingTemp_Rear              =[]         
LabOpPoint_RotorTemp                     =[]  
%=[]
variable_names = who; % 작업공간의 변수 이름들 가져오기
LabOpPoint_names = {}; % LabOpPoint 문자열이 포함된 변수 이름들을 저장할 셀 배열

for i = 1:numel(variable_names)
    if contains(variable_names{i}, 'LabOpPoint') % 변수 이름 검사
        LabOpPoint_names{end+1} = variable_names{i}; % 해당 변수 이름 저장
    end
end

LabOp_struct(1) = struct(); % 구조체 생성
LabOp_struct(2) = struct(); % 구조체 생성
for j=1:2
for i = 1:numel(LabOpPoint_names)
    LabOp_struct(j).(LabOpPoint_names{i}) = eval(LabOpPoint_names{i}); % 구조체에 필드 추가
end
end

%% Proximiti_Loss
Proximiti_Loss=struct();
Proximiti_Loss.HybridModel_PolynomialPower                 =[];           
Proximiti_Loss.HybridModel_TotalLines                      =[];      
Proximiti_Loss.HybridModel_FEAFluxLinePoints               =[];             
Proximiti_Loss.ArmatureCopperFreqCompLoss                  =[];          
Proximiti_Loss.FEAProxLoss_Turns                           =[]; 
Proximiti_Loss.FEAProxLosses_OC_Total                      =[];      
Proximiti_Loss.FEAProxLosses_OnLoad_Total                  =[];          
Proximiti_Loss.HybridAdjustmentFactor_ACLosses             =[];               
    
% Import;
Proximiti_Loss_names = {}; % 

% Import Result
Proximiti_Loss_names=fieldnames(Proximiti_Loss);
for fieldIndex=1:length(Proximiti_Loss_names)
    [success,charTypeData]=mcad.GetVariable(Proximiti_Loss_names{fieldIndex});
    Proximiti_Loss.(Proximiti_Loss_names{fieldIndex}) =  charTypeData;
end

% Set Magnetics
for fieldIndex=1:length(Proximiti_Loss_names)
    mcad.SetVariable(Proximiti_Loss_names{fieldIndex},Proximiti_Loss.(Proximiti_Loss_names{fieldIndex}));
end
%% Lab>Calculation>General



%Drive
mcad.SetVariable('DCBusVoltage',DCBusVoltage)
mcad.SetVariable('ModulationIndex_MotorLAB',ModulationIndex_MotorLAB)
%Operating Mode
%Control Strategy
mcad.SetVariable('ControlStrat_MotorLAB',ControlStrat_MotorLAB)

mcad.SetVariable('NumControlStrategyPoints_Lab',NumControlStrategyPoints_Lab)
mcad.SetVariable('ControlStrat_Speed_Lab',ControlStrat_Speed_Lab)
mcad.SetVariable('ControlStrat_PhaseAdvance_Lab',ControlStrat_PhaseAdvance_Lab)


% Losses




% Temperatures
% Stator Winding Temp
mcad.SetVariable('TwindingCalc_MotorLAB',TwindingCalc_MotorLAB)

% Ac Loss Temp Scaling
mcad.SetVariable('StatorCopperFreqCompTempExponent',StatorCopperFreqCompTempExponent)

% Magnet
mcad.SetVariable('TmagnetCalc_MotorLAB',TmagnetCalc_MotorLAB)
% Mech Loss
mcad.SetVariable('Airgap_Temperature',Airgap_Temperature)
mcad.SetVariable('Bearing_Temperature_F',Bearing_Temperature_F)
mcad.SetVariable('Bearing_Temperature_R',Bearing_Temperature_R)


%% Lab>Operating Point
mcad.SetVariable('OpPointSpec_MotorLAB',OpPointSpec_MotorLAB)
mcad.SetVariable('SpeedDemand_MotorLAB',SpeedDemand_MotorLAB)

if OpPointSpec_MotorLAB == 3
    mcad.SetVariable('StatorCurrentDemand_Lab',StatorCurrentDemand_Lab)
    mcad.SetVariable('PhaseAdvanceDemand_Lab',PhaseAdvanceDemand_Lab)
elseif OpPointSpec_MotorLAB == 0
    mcad.SetVariable('SpeedDemand_MotorLAB',TorqueDemand_MotorLAB)
elseif  OpPointSpec_MotorLAB == 1
        mcad.SetVariable('StatorCurrentDemand_Lab',StatorCurrentDemand_Lab)
elseif  OpPointSpec_MotorLAB == 2
             mcad.SetVariable('StatorCurrentDemand_Lab',StatorCurrentDemand_Lab)
end

mcad.CalculateOperatingPoint_Lab()

% Import Result
LabOpFieldsName=fieldnames(LabOpPoint_struct);
for fieldIndex=1:length(fieldnames(LabOpPoint_struct))
    [success,charTypeData]=mcad.GetVariable(LabOpFieldsName{fieldIndex});
    LabOpPoint_struct.(LabOpFieldsName{fieldIndex}) =  charTypeData;
end


