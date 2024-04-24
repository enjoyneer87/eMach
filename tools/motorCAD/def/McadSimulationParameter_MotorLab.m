function variable=McadSimulationParameter_MotorLab(fileName)
    variable=struct()
    %% Drive
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
    
    %%Electromagnetic 

    %% Thermal 

    variable.ThermalEnvelopeSensitivity_Lab          =    []                  
    variable.StatorTempDemand_Lab                    =    []        
    variable.RotorTempDemand_Lab                     =    []       
    variable.SpeedDemand_MotorLAB                    =    1000        
    variable.TorqueDemand_MotorLAB                   =    []         
    variable.PhaseAdvanceDemand_Lab                  =    45          
    variable.StatorCurrentDemand_Lab                 =    400           
    variable.StatorCurrentDemand_RMS_Lab             =    []               
    variable.RotorCurrentDemand_Lab                  =    []          
    variable.MaxNumAltStartPoints_Lab                =    []            
    variable.SlipDemand_Lab                          =    []  
    variable.OpPointSpec_MotorLAB                    =3 % 0 Torque 1: Maximum Current 2: Maximum Temperature 3: Current
    variable.LabThermalCoupling                     =[]
    variable.LabMagneticCoupling                    =[]
    
    %% Duty Cycle

    %% Operating Point 

    %% Generator

    %% Calibration

    %% Setting

    
    % Import;
    SimulationParameter_MotorLab_names = {}; % 
end