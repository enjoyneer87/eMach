function variable=McadLABCalcPackage(fileName)
    variable=struct();
    %% Calculation
    % >General
    % Drive
    variable.DCBusVoltage                                        =[];              
    variable.ModulationIndex_MotorLAB                            =[]; 
    % operating Mode
    variable.OperatingMode_Lab                       =    []     
    variable.ControlStrat_MotorLAB                   =    [] 
    % if Control Strategy is 3 enter below
    variable.NumControlStrategyPoints_Lab            =    []                
    variable.ControlStrat_Speed_Lab                  =    []          
    variable.ControlStrat_PhaseAdvance_Lab           =    [] 
    % DC Current Limit
    variable.DCCurrentLimit_Lab                      =    []   
    % if DC Current Limit is 1 enter below
    variable.MaxDCCurrent_Lab                        =    []  
    
    % Loss
    variable.StatorIronLossBuildFactor               =[] ;                  
    variable.RotorIronLossBuildFactor                =[] ;                  
    variable.MagnetLossBuildFactor                   =[] ;              
    % Scaling                                   
    % Turns/Coil                                    
    variable.TurnsCalc_MotorLAB                      =[];           
    variable.TurnsRef_MotorLAB                       =[];           
    % Active Length                                 
    variable.Length_Ref_Lab                          =[];       
    variable.Length_Ref_Resistance_Lab               =[];                   
    variable.Length_Calc_Lab                         =[];           
    % Temperature                                   
    % Stator Winding              
    % variable.Twdg_MotorLAB                        =[];           %ThermalParameters_MotorLAB
    
    variable.TwindingCalc_MotorLAB                   =[];          %ModelParameters_MotorLAB
    
    % AC loss Temperature Scaling                            
    variable.WindingTemp_ACLoss_Ref_Lab              =[];          %ThermalParameters_MotorLAB
    variable.StatorCopperFreqCompTempExponent        =[];                              
    % Magnet Temperature                                 
    % variable.
    variable.Tmag_MotorLAB                           =[];         %ThermalParameters_MotorLAB
    variable.TmagnetCalc_MotorLAB                    =[];         %ModelParameters_MotorLAB      
    % Mechanical Loss Temperatures                                  
    variable.Airgap_Temperature                      =[];          % Magnetics 
    variable.Bearing_Temperature_F                   =[];          % Magnetics      
    variable.Bearing_Temperature_R                   =[];          % Magnetics     
    
    %[TB]> Windage 

    %[TB]> Bearings

    %[TB]> Custom Losses


    %% Electromagnetic 
    variable.EmagneticCalcType_Lab                     =[];        
    variable.PowerLim_MotorLAB                         =[];                         %     % If EmagneticCalcType_Lab =1
    variable.PowerLimVal_MotorLAB                      =[];                         %      % if PowerLim_MotorLAB=1
    variable.SpeedMax_MotorLAB                         =[];    
    variable.Speedinc_MotorLAB                         =[];    
    variable.SpeedMin_MotorLAB                         =[];    
    variable.Imax_MotorLAB                             =[]; 
    variable.Imax_RMS_MotorLAB                         =[];    
    variable.Iinc_MotorLAB                             =[]; 
    variable.Imin_MotorLAB                             =[]; 
    variable.Imin_RMS_MotorLAB                         =[];    
    variable.TorqueMax_MotorLAB                        =[];    
    variable.TorqueInc_MotorLAB                        =[];    
    variable.MinTorque_MotorLAB                        =[];    

    %% Thermal 
    ThermalMapType_Lab
    ThermCalcType_MotorLAB
    TempLimit_MotorLAB
    MaxWindingSpec_MotorLAB

    MaxSpeedTherm_MotorLAB
    SpeedStepTherm_MotorLAB
    MinSpeedTherm_Lab
    MaxWindTemp_MotorLAB

    ThermMaxCurrentLim_MotorLAB
    Imax_MotorLAB
    Imax_RMS_MotorLAB

    Iest_MotorLAB
    Iest_RMS_MotorLAB

    
    % variable.ThermalEnvelopeSensitivity_Lab          =    []                  
    % variable.StatorTempDemand_Lab                    =    []        
    % variable.RotorTempDemand_Lab                     =    []       
    % variable.SpeedDemand_MotorLAB                    =    1000        
    % variable.TorqueDemand_MotorLAB                   =    []         
    % variable.PhaseAdvanceDemand_Lab                  =    45          
    % variable.StatorCurrentDemand_Lab                 =    400           
    % variable.StatorCurrentDemand_RMS_Lab             =    []               
    % variable.RotorCurrentDemand_Lab                  =    []          
    % variable.MaxNumAltStartPoints_Lab                =    []            
    % variable.SlipDemand_Lab                          =    []  
    % variable.OpPointSpec_MotorLAB                    =3 % 0 Torque 1: Maximum Current 2: Maximum Temperature 3: Current
    % variable.LabThermalCoupling                     =[]
    % variable.LabMagneticCoupling                    =[]
    
    %% Duty Cycle
    DutyCycleType_Lab                          =[]; 
    LabThermalCoupling_DutyCycle               =[];             
    
    % Vehicle Model
    Mass_MotorLAB      =[];         %   Mass
    K_r_MotorLAB       =[];         %   Rolling Resistance
    rho_MotorLAB       =[];         %   Air Density
    B_cont_MotorLAB    =[];         %   Generating Torque Ratio
    A_f_MotorLAB       =[];         %   Frontal Area
    C_d_MotorLAB       =[];         %   Drag Coefficient
    N_d_MotorLAB       =[];         %   Gear Ratio
    R_w_MotorLAB       =[];         %   Wheel Radius 
    WheelInertia       =[];         %   Wheel Inertia
    M_o_MotorLAB       =[];         %   Mass Correction Factor
    T_cont_MotorLAB    =[];         %   Motoring Torque Ratio
    SpeedCap_MotorLAB  =[];         %   Max Speed


    %% Operating Point 


    %% Generator

    %% Calibration

    %% Setting

    
    % Import;
    SimulationParameter_MotorLab_names = {}; % 
end