function [BuildingData]=devExportSatuMapFromMCADLabModel(SatuMapFilePath,mcad,SaturationMap_InputDefinition,stepSize1,stepSize2)

%% Get Lab Model Data
BuildingData.MotorCADGeo=tempDefMCADMachineData4Scaling(mcad);

[~,referenceSpeed   ]          =mcad.GetVariable('FEALossMap_RefSpeed_Lab' );
[~,SpeedMax_MotorLAB]          =mcad.GetVariable('SpeedMax_MotorLAB');
[~,CurrentSpec_MotorLAB]       =mcad.GetVariable('CurrentSpec_MotorLAB');
if CurrentSpec_MotorLAB==0
    [~,Imaxpk             ]          =mcad.GetVariable('MaxModelCurrent_MotorLAB');
    Imaxrms= Imaxpk/sqrt(2);
    Imax=Imaxpk;
elseif double(CurrentSpec_MotorLAB)==1    
    [~,Imaxrms             ]          =mcad.GetVariable('MaxModelCurrent_RMS_MotorLAB');
    Imaxpk = Imaxrms*sqrt(2);
    Imax=Imaxrms;
end
% [~,Imax]          =mcad.GetVariable('MaxModelCurrent_MotorLAB');
BuildingData.MotorCADGeo.Imaxpk              = Imaxpk             ;
BuildingData.MotorCADGeo.Imaxrms             = Imaxrms             ;
BuildingData.MotorCADGeo.referenceSpeed    = referenceSpeed   ;
BuildingData.MotorCADGeo.SpeedMax_MotorLAB = SpeedMax_MotorLAB;
BuildingData.MotorCADGeo.LabMaxRMSCurrentDensity =calcCurrentDensity(Imaxrms,double(BuildingData.MotorCADGeo.ParallelPaths),double(BuildingData.MotorCADGeo.NumberStrandsHand),BuildingData.MotorCADGeo.ArmatureConductorCSA);

%% Lab Model Build 정보
[~,BuildingData.Twdg_MotorLAB]                        =mcad.GetVariable('Twdg_MotorLAB'                     )   ;                             
[~,BuildingData.TwindingCalc_MotorLAB]                =mcad.GetVariable('TwindingCalc_MotorLAB'             ) ;                                               
[~,BuildingData.WindingTemp_ACLoss_Ref_Lab]           =mcad.GetVariable('WindingTemp_ACLoss_Ref_Lab'        )   ;                                                          
[~,BuildingData.Tmag_MotorLAB]                        =mcad.GetVariable('Tmag_MotorLAB'                     )   ;                             
[~,BuildingData.TmagnetCalc_MotorLAB]                 =mcad.GetVariable('TmagnetCalc_MotorLAB'              ) ;                   
[~,BuildingData.Airgap_Temperature]                   =mcad.GetVariable('Airgap_Temperature'                )   ;                                          
[~,BuildingData.Bearing_Temperature_F]                =mcad.GetVariable('Bearing_Temperature_F'             )   ;             
[~,BuildingData.Bearing_Temperature_R]                =mcad.GetVariable('Bearing_Temperature_R'             )   ;       

%
[~,BuildingData.coeffi.HybridAdjustmentFactor_ACLosses]      =mcad.GetVariable('HybridAdjustmentFactor_ACLosses'             ) ;                                                
[~,BuildingData.coeffi.WindingAlpha_MotorLAB]                =mcad.GetVariable('WindingAlpha_MotorLAB'             ) ;                                                
[~,BuildingData.coeffi.StatorCopperFreqCompTempExponent]     =mcad.GetVariable('StatorCopperFreqCompTempExponent'  ) ;                                                                       
[~,BuildingData.coeffi.BrTempCoeff_MotorLAB]                 =mcad.GetVariable('BrTempCoeff_MotorLAB'              ) ;                                               

 % Loss Model
[~,BuildingData.Resistance_MotorLAB       ]      =mcad.GetVariable('Resistance_MotorLAB');
[~,BuildingData.EndWindingResistance_Lab  ]      =mcad.GetVariable('EndWindingResistance_Lab');        
[~,BuildingData.EndWindingInductance_Lab  ]      =mcad.GetVariable('EndWindingInductance_Lab');     
%% Lab Calc 정보
[~,BuildingData.PostCalcTemp.TwindingCalc_MotorLAB]                =mcad.GetVariable('TwindingCalc_MotorLAB'             );                                                  
[~,BuildingData.PostCalcTemp.TmagnetCalc_MotorLAB]                 =mcad.GetVariable('TmagnetCalc_MotorLAB'              );                      
[~,a]=mcad.GetVariable('CurrentMotFilePath_MotorLAB');
BuildingData.CurrentMotFilePath_MotorLAB={a};
BuildingData.T0data.Twdg_MotorLAB=BuildingData.Twdg_MotorLAB;
BuildingData.T0data.Resistance_MotorLAB=BuildingData.Resistance_MotorLAB;
BuildingData.T0data.EndWindingResistance_Lab=BuildingData.EndWindingResistance_Lab;
BuildingData.T0data.ResistanceActivePart=BuildingData.Resistance_MotorLAB-BuildingData.EndWindingResistance_Lab;

%% Lossparameter
% RacRdc_MotorLAB
[~,BuildingData.RacRdc_MotorLAB]                 =mcad.GetVariable('RacRdc_MotorLAB'              );                      

%% SaturationMap Export

SaturationMap_PhaseAdvanceMax=90;
if nargin<3
    stepSize1=100;  
    % SaturationMap_InputDefinition=varargin{1};
    SaturationMap_InputDefinition=1;  
    mcad.SetVariable('SaturationMap_InputDefinition',       SaturationMap_InputDefinition);
    mcad.SetVariable('SaturationMap_CalculationMethod',     0);
    mcad.SetVariable('SaturationMap_Current_D_Max',       0);
    mcad.SetVariable('SaturationMap_Current_D_Step',      Imaxpk/stepSize1);
    mcad.SetVariable('SaturationMap_Current_D_Min',       -Imaxpk);
    mcad.SetVariable('SaturationMap_Current_Q_Max',       Imaxpk);
    mcad.SetVariable('SaturationMap_Current_Q_Step',      Imaxpk/stepSize1);
    mcad.SetVariable('SaturationMap_Current_Q_Min',       0);
elseif nargin==4
    if SaturationMap_InputDefinition==0
    mcad.SetVariable('SaturationMap_InputDefinition',       SaturationMap_InputDefinition);
    mcad.SetVariable('SaturationMap_CalculationMethod',     0);
    mcad.SetVariable('SaturationMap_StatorCurrentMax',      Imaxpk);
    mcad.SetVariable('SaturationMap_StatorCurrentStep',     Imaxpk/stepSize1);
    mcad.SetVariable('SaturationMap_StatorCurrentMin',      0);
    mcad.SetVariable('SaturationMap_PhaseAdvanceMax',       SaturationMap_PhaseAdvanceMax);
    mcad.SetVariable('SaturationMap_PhaseAdvanceStep',      SaturationMap_PhaseAdvanceMax/stepSize2);
    mcad.SetVariable('SaturationMap_PhaseAdvanceMin',       0);
    else
    mcad.SetVariable('SaturationMap_CalculationMethod',   0);
    mcad.SetVariable('SaturationMap_Current_D_Max',       0);
    mcad.SetVariable('SaturationMap_Current_D_Step',      Imaxpk/stepSize1);
    mcad.SetVariable('SaturationMap_Current_D_Min',       -Imaxpk);
    mcad.SetVariable('SaturationMap_Current_Q_Max',       Imaxpk);
    mcad.SetVariable('SaturationMap_Current_Q_Step',      Imaxpk/stepSize1);
    mcad.SetVariable('SaturationMap_Current_Q_Min',       0);
    end
end
mcad.SetVariable('SaturationMap_Export',      1);
mcad.SetVariable('LossMap_Export',            1);
mcad.SetVariable('LossMap_Speed',             referenceSpeed);

mcad.SetVariable('SaturationMap_ExportFile',            SatuMapFilePath);
mcad.CalculateSaturationMap();
satuMapData=load(SatuMapFilePath);
BuildingData.satuMapData=satuMapData;
clear('mcad','referenceSpeed','Imax','Imaxrms','Imaxpk','ans','SpeedMax_MotorLAB')
save(SatuMapFilePath,'BuildingData','-mat');
end