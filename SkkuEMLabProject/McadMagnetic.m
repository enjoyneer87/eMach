function variable=McadMagnetic(fileName)
    variable=struct();
    % Temperature
    variable.Airgap_Temperature                                  =[];
    variable.Bearing_Temperature_F                               =[];  
    variable.Magnet_Temperature                                  =[];
    variable.Bearing_Temperature_R                               =[];  
    variable.Shaft_Temperature                                   =[];
    variable.ArmatureConductor_Temperature                       =[];      
    % Drive
    variable.DCBusVoltage                                        =[];              
    variable.ModulationIndex_MotorLAB                            =[];                                                                 
    % Build Factor                                      =[]          ;      
    variable.IronLossBuildFactorDefinition                       =[];                               
    variable.StatorIronLossBuildFactor                           =[];                            
    variable.RotorIronLossBuildFactor                            =[];                          
    variable.HysteresisLossBuildFactor                           =[];                           
    variable.EddyLossBuildFactor                                 =[];                     
    variable.MagnetLossBuildFactor                               =[];                                                               
    variable.BMax_StatorBackIron_Static                          =[];                            
    variable.BMax_StatorBackIron_Static                          =[];                                                                            
    % Ac loss                                           =[]          ; 
    variable.ACConductorLoss_MagneticMethod                      =[];                                
    variable.ACConductorLoss_MagneticMethod_L                    =[];                                  
    variable.ACConductorLoss_MagneticMethod_R                    =[];                                  
    variable.ACConductorLoss_FluxDensity                         =[];                             
    variable.ACConductorLoss_FluxDensity_L                       =[];                               
    variable.ACConductorLoss_FluxDensity_R                       =[];                               
    variable.ACConductorLossProportion                           =[];                           
    variable.ACConductorLossRatio_OldMethod                      =[];                                
    variable.ACConductorLossRatio_NewMethod                      =[];                                
    variable.ACConductorLossUserValues                           =[];                           
    variable.ACConductorLossUserRatio                            =[];                          
    variable.ACConductorLoss_MagneticMethod_Total                =[];                                      
    variable.ACConductorLoss_MagneticMethod_Total_L              =[];                                        
    variable.ACConductorLoss_MagneticMethod_Total_R              =[];     
    % Import;
    Magnetics_names = {}; % 
end