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

    %%%%%%%%%%%%%%%%%%%%%% Operating Point
    OpPointSpec_MotorLAB;
    SpeedDemand_MotorLAB;
    %Torque
    TorqueDemand_MotorLAB;
    %Maximum Current / Current/Phase Adcance
    StatorCurrentDemand_Lab;
    %Maximum Temperature
    StatorTempDemand_Lab;
    RotorTempDemand_Lab;
    %Current/Phase Adcance
    PhaseAdvanceDemand_Lab;

    LabThermalCoupling;
    LabMagneticCoupling;

    %%%%%%%%%%%%%%%%%%%%%% Generator
    Gen_Speed_Fixed_Lab;
    Gen_Speed_Max_Lab;
    %None Fixed Value
    Gen_Speed_Step_Lab
    Gen_Speed_Min_Lab
    Gen_Load_Connection_Lab

    Gen_Load_Definition_Lab

    %%Impedance/Power Factor
    Gen_Impedance_Fixed_Lab
    Gen_Impedance_Max_Lab

    %Load Impedance None Fixed Value
    Gen_Impedance_Step_Lab
    Gen_Impedance_Min_Lab

    Gen_PF_Fixed_Lab
    Gen_PF_Max_Lab
    %Load Power Factor None Fixed Value
    Gen_PF_Step_Lab
    Gen_PF_Min_Lab

    %%Resistance/Inductance
    Gen_Resistance_Fixed_Lab
    Gen_Resistance_Max_Lab

    %Load REsistance None
    Gen_Resistance_Step_Lab
    Gen_Resistance_Min_Lab

    Gen_Inductance_Fixed_Lab
    %Load Inductance
    Gen_Inductance_Max_Lab
    %None Fixed Value
    Gen_Inductance_Step_Lab
    Gen_Inductance_Min_Lab

    %%%%%%%%%%%%%%%%%%%%%% Calibration
    %%
    TestType_MotorLAB
    TestSpeedMax_MotorLAB
    TestSpeedInc_MotorLAB
    TestSpeedMin_MotorLAB

    ExpData_MotorLAB
    ExpDataType_MotorLAB

    %%%%%%%%%%%%%%%%%%%%%% Setting
    CurrentSpec_MotorLAB
    NonSalient_MotorLAB
    SaturationModelMethod_Lab
    %Inerpolation
    SaturationModelInterpolation_Lab

    XEndLeak_MotorLAB
    LEndWdg_MotorLAB

    IronLossBuildFactorDefinition
    ACConductorLossSplit_Lab


    
    % Import;
    variable_names = {}; % 
end