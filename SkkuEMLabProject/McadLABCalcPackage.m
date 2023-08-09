function variable=McadLABCalcPackage(fileName)
    variable=struct();

    %% Model Build
    %
    variable.ModelBuildSpeed_MotorLAB                   = 20000;    % Model Build - Parameters - Maximum speed
    variable.MaxModelCurrent_RMS_MotorLAB               = 500;      % Model Build - Parameters - Max stator current (RMS)
    variable.BuildSatModel_MotorLAB                     = true;     % Model Build - Build - Saturation Model : "On"
    variable.BuildLossModel_MotorLAB                    = true;     % Model Build - Build - Loss Model : "On"

    % Model Build - Model Option
    variable.LossModel_Lab                              = 2;        % Saturation Model - Model Type : Saturation Model (Full Cycle)
    variable.ModelType_MotorLAB                         = 1;        % Saturtion Model - Model Resolution : Fine (30 points)

    variable.LossModel_Lab                              = 1;        % Loss Model - Model Type : FEA Map (recommended)
    variable.ACLossMethod_Lab                           = 0;        % AC Loss Model - Model Type : Hybrid Method

    % Model Build - Loss Model


    % Model Build - Machine Parameters


    %% Calculation
    % Calculation - General
    variable.DCBusVoltage                               = 800;      % Drive - DC Bus Voltage
    variable.ModulationIndex_MotorLAB                   = 0.85;     % Drive - Maximum Modulation Index
    variable.OperatingMode_Lab                          = 0;        % Drive - Operating Mode : Motor
    variable.ControlStrat_MotorLAB                      = 0;        % Drive - Control Stratey : Maximum Torque/Amp
    variable.DCCurrentLimit_Lab                         = 0;        % Drive - DC Current Limit : None

    variable.MagnetLossBuildFactor                      = 1 ;       % Losses - Magnet Loss Build Factor           
    variable.StatorIronLossBuildFactor                  = 1 ;       % Losses - Iron Loss Build Factors - Stator                
    variable.RotorIronLossBuildFactor                   = 1 ;       % Losses - Iron Loss Build Factors - Rotor                

    variable.TurnsRef_MotorLAB                          = [];       % Scaling           
    variable.ResistanceTurnsRef_MotorLAB                = [];       % Scaling
    variable.TurnsCalc_MotorLAB                         = 1;        % Scaling - Turns / Coil - Calculation           

    variable.Length_Ref_Lab                             = [];       % Scaling       
    variable.Length_Ref_Resistance_Lab                  = [];       % Scaling                   
    variable.Length_Calc_Lab                            = [];       % Scaling - Active Length - Calculation           

    variable.TwindingCalc_MotorLAB                      = 65;       % Temperatures - Stator Winding Temperature - Calculation temperature
    variable.StatorCopperFreqCompTempExponent           = 1;        % Temperatures - Stator Winding Temperature - AC Loss Temperature Scailing - Temperature Exponent
    variable.TmagnetCalc_MotorLAB                       = 65;       % Temperatures - Magnet Temperature - Calculation temperature

    variable.NumControlStrategyPoints_Lab               = [];       %                  
    variable.ControlStrat_Speed_Lab                     = [];       %            
    variable.ControlStrat_PhaseAdvance_Lab              = [];       %   
    variable.MaxDCCurrent_Lab                           = [];       %  
    variable.WindingTemp_ACLoss_Ref_Lab                 = [];       % ThermalParameters_MotorLAB
    variable.Tmag_MotorLAB                              = [];       % ThermalParameters_MotorLAB
    variable.Airgap_Temperature                         = [];       % Magnetics 
    variable.Bearing_Temperature_F                      = [];       % Magnetics      
    variable.Bearing_Temperature_R                      = [];       % Magnetics     
    
    % Calculation - Windage 


    % Calculation - Bearings

    
    % Calculation - Custom Losses


    %% Electromagnetic 
    variable.EmagneticCalcType_Lab                      = 1;        % Calculation - Calculation Type : Efficiency Map        
    variable.SmoothMap_MotorLAB                         = true;     % Calculation - Options - Smooth Map : "On"
    variable.PowerLim_MotorLAB                          = false;    % Calculation - Options - Power Limit : "Off"
    variable.SpeedMax_MotorLAB                          = 25000;    % Calculation - Speed - Maximum    
    variable.Speedinc_MotorLAB                          = 200;      % Calculation - Speed - Step Size
    variable.SpeedMin_MotorLAB                          = 100;      % Calculation - Speed - Minimum
    variable.Imax_MotorLAB                              = [];       % 
    variable.Imax_RMS_MotorLAB                          = 500;      % Calculation - Current - Maximum (RMS)
    variable.Iinc_MotorLAB                              = 10;       % Calculation - Current - No. of Increments
    variable.Imin_MotorLAB                              = [];       % 
    variable.Imin_RMS_MotorLAB                          = 10;       % Calculation - Current - Minimum (RMS)
    variable.TorqueMax_MotorLAB                         = [];       %    
    variable.TorqueInc_MotorLAB                         = [];       %    
    variable.MinTorque_MotorLAB                         = [];       %    

    %% Thermal
    variable.ThermalMapType_Lab                         = 0;        % Calculation - Thermal Map Type : Envelope
    variable.ThermCalcType_MotorLAB                     = 0;        % Calculation - Thermal Calculation : Steady State
    variable.TempLimit_MotorLAB                         = 0;        % Calculation - Thermal Limit - Stator and Magnet : Stator Winding Only
    variable.MaxWindingSpec_MotorLAB                    = 0;        % Calculation - Thermal Limit - Maximum Winding Node : Average
    variable.MaxSpeedTherm_MotorLAB                     = 25000;    % Calculation - Speed - Maximum
    variable.SpeedStepTherm_MotorLAB                    = 500;      % Calculation - Speed - Step Size
    variable.MinSpeedTherm_Lab                          = 50;       % Calculation - Speed - Minimum
    variable.MaxWindTemp_MotorLAB                       = 180;      % Calculation - Maximum Temperatures - Stator Winding
    variable.ThermMaxCurrentLim_MotorLAB                = false;    % Calculation - Max. Current - Limit on Max. Current : "Off"
    variable.Iest_MotorLAB                              = [];       % Calculation - Initial Current Estimate - Stator Current (Peak)
    variable.Iest_RMS_MotorLAB                          = 500;      % Calculation - Initial Current Estimate - Stator Current (RMS)
   
    variable.ThermalEnvelopeSensitivity_Lab             = [];                  
    variable.StatorTempDemand_Lab                       = [];        
    variable.RotorTempDemand_Lab                        = [];       
    variable.SpeedDemand_MotorLAB                       = 1000;        
    variable.TorqueDemand_MotorLAB                      = [];         
    variable.PhaseAdvanceDemand_Lab                     = 45;          
    variable.StatorCurrentDemand_Lab                    = 400;           
    variable.StatorCurrentDemand_RMS_Lab                = [];               
    variable.RotorCurrentDemand_Lab                     = [];          
    variable.MaxNumAltStartPoints_Lab                   = [];            
    variable.SlipDemand_Lab                             = [];  
    variable.OpPointSpec_MotorLAB                       = 3; % 0 Torque 1: Maximum Current 2: Maximum Temperature 3: Current
    variable.LabThermalCoupling                         = [];
    variable.LabMagneticCoupling                        = [];
    
    %% Duty Cycle
    % Calculation
    variable.DutyCycleType_Lab                          = 1;        % Duty Cycle - Duty Cycle Type : Automotive Drive Cycle 
    variable.DrivCycle_MotorLAB                         = 18;       % Duty Cycle - Automotive Drive Cycle : WLTP Class 3 
    variable.LabThermalCoupling_DutyCycle               = 0;        % Duty Cycle - Thermal Transient Coupling : No coupling (default)

    variable.Mass_MotorLAB                              = [];       % Vehicle Model - Mass
    variable.K_r_MotorLAB                               = [];       % Vehicle Model - Rolling Resistance
    variable.rho_MotorLAB                               = [];       % Vehicle Model - Air Density
    variable.B_cont_MotorLAB                            = [];       % Vehicle Model - Generating Torque Ratio
    variable.A_f_MotorLAB                               = [];       % Vehicle Model - Frontal Area
    variable.C_d_MotorLAB                               = [];       % Vehicle Model - Drag Coefficient
    variable.N_d_MotorLAB                               = [];       % Vehicle Model - Gear Ratio
    variable.TorqueCapTrue_MotorLAB                     = false;    % Vehicle Model - Max. Torque : "Off"
    variable.TorqueCap_MotorLAB                         = [];       % Vehicle Model - Max. Torque
    variable.R_w_MotorLAB                               = [];       % Vehicle Model - Wheel Radius 
    variable.WheelInertia                               = [];       % Vehicle Model - Wheel Inertia
    variable.M_o_MotorLAB                               = [];       % Vehicle Model - Mass Correction Factor
    variable.T_cont_MotorLAB                            = [];       % Vehicle Model - Motoring Torque Ratio
    variable.SpeedCapTrue_MotorLAB                      = false;    % Vehicle Model - Max. Speed
    variable.SpeedCap_MotorLAB                          = [];       % Vehicle Model - Max. Speed

    % Duty Cycle Definition


    %% Operating Point 
    variable.OpPointSpec_MotorLAB                       = 0;        % Calculation - Input - Definition : Torque
    variable.SpeedDemand_MotorLAB                       = [];       % Calculation - Input - Speed
    variable.TorqueDemand_MotorLAB                      = [];       % Calculation - Input - Torque
    variable.LabThermalCoupling                         = 0;        % Calculation - Linkage Options - Lab <-> Thermal Coupling : No coupling (default)
    variable.LabMagneticCoupling                        = 0;        % Calculation - Linkage Options - Lab <-> E-Magnetic Coupling : No coupling (default)


    %% Generator


    %% Calibration


    %% Setting
    variable.CurrentSpec_MotorLAB                       = 1;        % Input Settings - Current/Voltage Definition : RMS

    variable.NonSalient_MotorLAB                        = false;    % Model Settings - Non Salient : "Off"
    variable.SaturationModelMethod_Lab                  = 0;        % Model Settings - Saturation Model Method : Curve Fit (default)

    variable.XEndLeak_MotorLAB                          = 1;        % Adjustment Factors - Magnet Flux Adjustment
    variable.LEndWdg_MotorLAB                           = 0;        % Adjustment Factors - Additional EWdg Inductance

    variable.IronLossBuildFactorDefinition              = 0;        % Losses - Iron Loss Build Factor Definition : Stator / Rotor (default)
    variable.ACConductorLossSplit_Lab                   = 0;        % Losses - AC Winding Loss Deistribution : Automatic (default)
    
    % SimulationParameter_MotorLab_names = {}; % 


end