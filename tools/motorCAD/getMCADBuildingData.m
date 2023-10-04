function BuildingData=getMCADBuildingData(mcad)
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
    
    %
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
    BuildingData.CurrentMotFilePath_MotorLAB={a}
    %% Data sort By Temperature
    BuildingData.T0data.Twdg_MotorLAB=BuildingData.Twdg_MotorLAB;
    BuildingData.T0data.Resistance_MotorLAB=BuildingData.Resistance_MotorLAB;
    BuildingData.T0data.EndWindingResistance_Lab=BuildingData.EndWindingResistance_Lab;
    BuildingData.T0data.ResistanceActivePart=BuildingData.Resistance_MotorLAB-BuildingData.EndWindingResistance_Lab;
end