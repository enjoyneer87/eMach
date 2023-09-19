function input = devDefVehicleVariable()
%% 값 수정해서 사용
    input.DutyCycleType_Lab                         = 1;        
    input.DrivCycle_MotorLAB                        = 17;       
    input.LabThermalCoupling_DutyCycle              = 0;        
    if input.LabThermalCoupling_DutyCycle == 2
        input.Transient_Number_Cycles               = 1;        
    end
    input.Mass_MotorLAB                             = 2162;     
    input.K_r_MotorLAB                              = 0.0054;   
    input.rho_MotorLAB                              = 1.225;    
    input.B_cont_MotorLAB                           = 1;        
    input.A_f_MotorLAB                              = 2.4978;   
    input.C_d_MotorLAB                              = 0.208;    
    % input.N_d_MotorLAB                              = [];       
    input.TorqueCapTrue_MotorLAB                    = false;    
    if input.TorqueCapTrue_MotorLAB || input.TorqueCapTrue_MotorLAB == 1
        input.TorqueCap_MotorLAB                    = [];       
    end
    input.R_w_MotorLAB                              = 0.3552;   
    input.WheelInertia                              = 0;        
    input.M_o_MotorLAB                              = 1.04;     
    input.T_cont_MotorLAB                           = 1;        
    input.SpeedCapTrue_MotorLAB                     = false;    
    if input.SpeedCapTrue_MotorLAB || input.SpeedCapTrue_MotorLAB == 1
        input.SpeedCap_MotorLAB                     = [];       
    end
end