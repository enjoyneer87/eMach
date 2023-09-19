function [MotorCADGeo,SatuMapData,BuildingData]=devExportSatuMapFromMCADLabModel(SatuMapFilePath,mcad,varargin)


%% Get Lab Model Data
MotorCADGeo=tempDefMCADMachineData4Scaling(mcad);

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
MotorCADGeo.Imaxpk              = Imaxpk             ;
MotorCADGeo.Imaxrms             = Imaxrms             ;
MotorCADGeo.referenceSpeed    = referenceSpeed   ;
MotorCADGeo.SpeedMax_MotorLAB = SpeedMax_MotorLAB;
MotorCADGeo.LabMaxRMSCurrentDensity =calcCurrentDensity(Imaxrms,double(MotorCADGeo.ParallelPaths),double(MotorCADGeo.NumberStrandsHand),MotorCADGeo.ArmatureConductorCSA);

%% Lab Model Build 정보
[~,BuildingData.Twdg_MotorLAB]                        =mcad.GetVariable('Twdg_MotorLAB'                     )   ;                             
% [~,BuildingData.TwindingCalc_MotorLAB]                =mcad.GetVariable('TwindingCalc_MotorLAB'             ) ;                                               
% [~,BuildingData.WindingAlpha_MotorLAB]                =mcad.GetVariable('WindingAlpha_MotorLAB'             ) ;                                               
[~,BuildingData.WindingTemp_ACLoss_Ref_Lab]           =mcad.GetVariable('WindingTemp_ACLoss_Ref_Lab'        )   ;                                                          
% [~,BuildingData.StatorCopperFreqCompTempExponent]     =mcad.GetVariable('StatorCopperFreqCompTempExponent'  )  ;                                                                      
[~,BuildingData.Tmag_MotorLAB]                        =mcad.GetVariable('Tmag_MotorLAB'                     )   ;                             
% [~,BuildingData.TmagnetCalc_MotorLAB]                 =mcad.GetVariable('TmagnetCalc_MotorLAB'              ) ;                   
% [~,BuildingData.BrTempCoeff_MotorLAB]                 =mcad.GetVariable('BrTempCoeff_MotorLAB'              ) ;                                              
[~,BuildingData.Airgap_Temperature]                   =mcad.GetVariable('Airgap_Temperature'                )   ;                                          
[~,BuildingData.Bearing_Temperature_F]                =mcad.GetVariable('Bearing_Temperature_F'             )   ;             
[~,BuildingData.Bearing_Temperature_R]                =mcad.GetVariable('Bearing_Temperature_R'             )   ;       

%
[~,BuildingData.coeffi.WindingAlpha_MotorLAB]                =mcad.GetVariable('WindingAlpha_MotorLAB'             ) ;                                                
[~,BuildingData.coeffi.StatorCopperFreqCompTempExponent]     =mcad.GetVariable('StatorCopperFreqCompTempExponent'  ) ;                                                                       
[~,BuildingData.coeffi.BrTempCoeff_MotorLAB]                 =mcad.GetVariable('BrTempCoeff_MotorLAB'              ) ;                                               



%% Lab Calc 정보
[~,BuildingData.PostCalcTemp.TwindingCalc_MotorLAB]                =mcad.GetVariable('TwindingCalc_MotorLAB'             );                                                  
[~,BuildingData.PostCalcTemp.TmagnetCalc_MotorLAB]                 =mcad.GetVariable('TmagnetCalc_MotorLAB'              );                      

%%
if nargin>2
    SaturationMap_InputDefinition=varargin{1};
else 
    SaturationMap_InputDefinition=1;
end

mcad.SetVariable('SaturationMap_InputDefinition',       SaturationMap_InputDefinition);
mcad.SetVariable('SaturationMap_CalculationMethod',     0);



if SaturationMap_InputDefinition==0
mcad.SetVariable('SaturationMap_StatorCurrentMax',       Imax);
mcad.SetVariable('SaturationMap_StatorCurrentStep',      Imax/30);
mcad.SetVariable('SaturationMap_StatorCurrentMin',       0);
mcad.SetVariable('SaturationMap_PhaseAdvanceMax',       90);
mcad.SetVariable('SaturationMap_PhaseAdvanceStep',      5);
mcad.SetVariable('SaturationMap_PhaseAdvanceMin',       0);
elseif SaturationMap_InputDefinition==1
%
mcad.SetVariable('SaturationMap_Current_D_Max',       0);
mcad.SetVariable('SaturationMap_Current_D_Step',      Imax/100);
mcad.SetVariable('SaturationMap_Current_D_Min',       -Imax);
mcad.SetVariable('SaturationMap_Current_Q_Max',       Imax);
mcad.SetVariable('SaturationMap_Current_Q_Step',      Imax/100);
mcad.SetVariable('SaturationMap_Current_Q_Min',       0);
end
mcad.SetVariable('SaturationMap_Export',      1);
mcad.SetVariable('LossMap_Export',            1);
mcad.SetVariable('LossMap_Speed',             referenceSpeed);

mcad.SetVariable('SaturationMap_ExportFile',            SatuMapFilePath);
mcad.CalculateSaturationMap();
SatuMapData=load(SatuMapFilePath);
SatuMapData.BuildingData=BuildingData;
SatuMapData.MotorCADGeo=MotorCADGeo;
clear('mcad','referenceSpeed','Imax','Imaxrms','Imaxpk','ans','SpeedMax_MotorLAB')
save(SatuMapFilePath,'-mat');
end