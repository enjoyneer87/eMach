function variable=McadModelParameters_MotorLAB(fileName)
    variable=struct()
    % Matches 166 variable
    variable.FEALossMap_RefSpeed_Lab                             =[];
%
    variable.TmagnetCalc_MotorLAB                                = []    
    variable.TwindingCalc_MotorLAB                               = [] 
    variable.LabOpPoint_CustomThermalLimitsTemperatures          = []                      
    variable.RotorWindingTempCoeffResistivity_Lab                = []                
    variable.ResultsPath_MotorLAB                                = []
    
    variable.WindingAlpha_MotorLAB                               = [] 
    %                                
    variable.WindingTemp_ACLoss_Ref_Lab                          = []     
    %
    variable.ModulationIndex_MotorLAB                            =[];                            
    %
    variable.LabModel_ACLoss_Method                              =[];                          
    variable.LabModel_ACLoss_StatorCurrent_Peak                  =[];                                      
    variable.LabModel_ACLoss_StatorCurrent_RMS                   =[];                                     
    variable.LabModel_ACLoss_RotorCurrent                        =[];
    
    variable.LabModel_MagnetLoss_Date                            =[];                            
    variable.LabModel_MagnetLoss_Method                          =[];                              
    variable.LabModel_MagnetLoss_StatorCurrent_Peak              =[];                                          
    variable.LabModel_MagnetLoss_StatorCurrent_RMS               =[];  
    variable.LossModel_AC_Lab                                    =[];


    % Import;
    variable_names = {}; % 
end