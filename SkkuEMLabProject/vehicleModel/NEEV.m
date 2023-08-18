function input = devDefVehicleVariable()
%% 값 수정해서 사용
    input.DutyCycleType_Lab                         = 1;        
    input.DrivCycle_MotorLAB                        = 17;       
    input.LabThermalCoupling_DutyCycle              = 0;        
    if input.LabThermalCoupling_DutyCycle == 2
        input.Transient_Number_Cycles               = 1;        
    end
    %Mass (기입)
    input.Mass_MotorLAB                             = 1800;     
    %Rolling resistance coefficient (고정)
    input.K_r_MotorLAB                              = 0.0054;   
    %Air density (고정)
    input.rho_MotorLAB                              = 1.225;    
    %Contribution of motor to negative torque points (고정)
    input.B_cont_MotorLAB                           = 1;        
    %Frontal area (기입)
    input.A_f_MotorLAB                              = 3.0335;   
    %Drag coefficient (기입)
    input.C_d_MotorLAB                              = 0.288;    
    %Gear ratio (final drive ratio) in the vehicle model (final drvie ratio 기입)
    %input.N_d_MotorLAB                              = [4.706];       
    input.TorqueCapTrue_MotorLAB                    = false;    
    if input.TorqueCapTrue_MotorLAB || input.TorqueCapTrue_MotorLAB == 1
        input.TorqueCap_MotorLAB                    = [];       
    end
    %Wheel radius (기입)
    input.R_w_MotorLAB                              = 0.7431;   
    %Inertia of all wheels on the vehicle (생략)
    input.WheelInertia                              = 0;        
    %Mass correction factor
    input.M_o_MotorLAB                              = 1.04;     
    %Contribution of motor to positive torque points
    input.T_cont_MotorLAB                           = 1;        
    input.SpeedCapTrue_MotorLAB                     = false;    
    if input.SpeedCapTrue_MotorLAB || input.SpeedCapTrue_MotorLAB == 1
        input.SpeedCap_MotorLAB                     = [];       
    end
end