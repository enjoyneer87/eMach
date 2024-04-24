function BuildingData=getMCADBuildingData(mcad)


%% MotorCADGeo Get Lab Model Data
BuildingData.MotorCADGeo=devDefMCADMachineData4Scaling(mcad);

[~,referenceSpeed   ]                   =mcad.GetVariable('FEALossMap_RefSpeed_Lab' );
[~,SpeedMax_MotorLAB]                   =mcad.GetVariable('SpeedMax_MotorLAB');
[~,CurrentSpec_MotorLAB]                =mcad.GetVariable('CurrentSpec_MotorLAB');
if CurrentSpec_MotorLAB==0
    [~,Imaxpk             ]             =mcad.GetVariable('MaxModelCurrent_MotorLAB');
    Imaxrms= Imaxpk/sqrt(2);
    Imax=Imaxpk;
elseif double(CurrentSpec_MotorLAB)==1    
    [~,Imaxrms             ]            =mcad.GetVariable('MaxModelCurrent_RMS_MotorLAB');
    Imaxpk = Imaxrms*sqrt(2);
    Imax=Imaxrms;
end
% [~,Imax]          =mcad.GetVariable('MaxModelCurrent_MotorLAB');
BuildingData.MotorCADGeo.Imaxpk                          = Imaxpk             ;
BuildingData.MotorCADGeo.Imaxrms                         = Imaxrms             ;

BuildingData.MotorCADGeo.referenceSpeed                  = referenceSpeed   ;
BuildingData.MotorCADGeo.FEALossMap_RefSpeed_Lab         = referenceSpeed;
BuildingData.MotorCADGeo.SpeedMax_MotorLAB               = SpeedMax_MotorLAB;
BuildingData.MotorCADGeo.LabMaxRMSCurrentDensity         =calcCurrentDensity(Imaxrms,double(BuildingData.MotorCADGeo.ParallelPaths),double(BuildingData.MotorCADGeo.NumberStrandsHand),BuildingData.MotorCADGeo.ArmatureConductorCSA);


%% Lab Model Build 정보
[~,BuildingData.Twdg_MotorLAB]                        =mcad.GetVariable('Twdg_MotorLAB'                     )   ;                             
[~,BuildingData.ArmatureConductor_Temperature]        =mcad.GetVariable('ArmatureConductor_Temperature'                     )   ;                                     
[~,BuildingData.TwindingCalc_MotorLAB]                =mcad.GetVariable('TwindingCalc_MotorLAB'             ) ;                                               
[~,BuildingData.WindingTemp_ACLoss_Ref_Lab]           =mcad.GetVariable('WindingTemp_ACLoss_Ref_Lab'        )   ;                                                          
[~,BuildingData.Tmag_MotorLAB]                        =mcad.GetVariable('Tmag_MotorLAB'                     )   ;                             
[~,BuildingData.TmagnetCalc_MotorLAB]                 =mcad.GetVariable('TmagnetCalc_MotorLAB'              ) ;                   
[~,BuildingData.Airgap_Temperature]                   =mcad.GetVariable('Airgap_Temperature'                )   ;                                          
[~,BuildingData.Bearing_Temperature_F]                =mcad.GetVariable('Bearing_Temperature_F'             )   ;             
[~,BuildingData.Bearing_Temperature_R]                =mcad.GetVariable('Bearing_Temperature_R'             )   ;       

% coeffi
[~,BuildingData.coeffi.HybridAdjustmentFactor_ACLosses]      =mcad.GetVariable('HybridAdjustmentFactor_ACLosses'             ) ;                                                
[~,BuildingData.coeffi.WindingAlpha_MotorLAB]                =mcad.GetVariable('WindingAlpha_MotorLAB'             ) ;                                                
[~,BuildingData.coeffi.StatorCopperFreqCompTempExponent]     =mcad.GetVariable('StatorCopperFreqCompTempExponent'  ) ;                                                                       
[~,BuildingData.coeffi.BrTempCoeff_MotorLAB]                 =mcad.GetVariable('BrTempCoeff_MotorLAB'              ) ;                                               

% Loss Model
[~,BuildingData.Resistance_MotorLAB       ]      =mcad.GetVariable('Resistance_MotorLAB');
[~,BuildingData.EndWindingResistance_Lab  ]      =mcad.GetVariable('EndWindingResistance_Lab');        
[~,BuildingData.EndWindingInductance_Lab  ]      =mcad.GetVariable('EndWindingInductance_Lab');        

%% LabBuildData
BuildingData.LabBuildData=defLabBuildData(mcad);
% [~,BuildingData.LabBuildData.n2ac_MotorLAB              ]=mcad.GetVariable('n2ac_MotorLAB'            );
% [~,BuildingData.LabBuildData.AcLossFreq_MotorLAB        ]=mcad.GetVariable('AcLossFreq_MotorLAB'      );
% [~,BuildingData.LabBuildData.MagLossCoeff_MotorLAB      ]=mcad.GetVariable('MagLossCoeff_MotorLAB'   );
% [~,BuildingData.LabBuildData.FEALossMap_RefSpeed_Lab    ]=mcad.GetVariable('FEALossMap_RefSpeed_Lab'  );
% [~,BuildingData.LabBuildData.BandingLossCoefficient_Lab ]=mcad.GetVariable('BandingLossCoefficient_Lab');


%% PostCalcTemp Lab Calc 정보
    [~,BuildingData.PostCalcTemp.TwindingCalc_MotorLAB]     =mcad.GetVariable('TwindingCalc_MotorLAB'             );                                                  
    [~,BuildingData.PostCalcTemp.TmagnetCalc_MotorLAB]      =mcad.GetVariable('TmagnetCalc_MotorLAB'              );                      
    [~,a]                                                   =mcad.GetVariable('CurrentMotFilePath_MotorLAB');
    BuildingData.CurrentMotFilePath_MotorLAB                ={a};
    %% Data sort By Temperature
    BuildingData.T0data.Twdg_MotorLAB           =BuildingData.Twdg_MotorLAB;
    BuildingData.T0data.Resistance_MotorLAB     =BuildingData.Resistance_MotorLAB;
    BuildingData.T0data.EndWindingResistance_Lab=BuildingData.EndWindingResistance_Lab;
    BuildingData.T0data.ResistanceActivePart    =BuildingData.Resistance_MotorLAB-BuildingData.EndWindingResistance_Lab;
%% Lossparameter
% RacRdc_MotorLAB
[~,BuildingData.RacRdc_MotorLAB]                 =mcad.GetVariable('RacRdc_MotorLAB'              );                      

end