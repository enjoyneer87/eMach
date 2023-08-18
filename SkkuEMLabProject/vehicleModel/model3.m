function input = model3()
%% 값 수정해서 사용
    input.DutyCycleType_Lab                         = 1;        
    input.DrivCycle_MotorLAB                        = 17;       
    input.LabThermalCoupling_DutyCycle              = 0;        
    if input.LabThermalCoupling_DutyCycle == 2
        input.Transient_Number_Cycles               = 1;        
    end
    %Mass (기입)
    input.Mass_MotorLAB                             = 1928;     
    %Rolling resistance coefficient (고정)
    input.K_r_MotorLAB                              = 0.0054;   
    %Air density (고정)
    input.rho_MotorLAB                              = 1.225;    
    %Contribution of motor to negative torque points (고정)
    input.B_cont_MotorLAB                           = 1;        
    %Frontal area (기입)
    input.A_f_MotorLAB                              = 2.6681;   
    %Drag coefficient (기입)
    input.C_d_MotorLAB                              = 0.23;    
    %Gear ratio (final drive ratio) in the vehicle model (final drvie ratio 기입)
    %input.N_d_MotorLAB                              = [9];       
    input.TorqueCapTrue_MotorLAB                    = false;    
    if input.TorqueCapTrue_MotorLAB || input.TorqueCapTrue_MotorLAB == 1
        input.TorqueCap_MotorLAB                    = [];       
    end
    %Wheel radius (기입)
    input.R_w_MotorLAB                              = 0.4915;   
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
    %% 수정  x
    
    % 필드가 있는지 확인하고 필요할 때만 테이블에 추가
    data = {
        "DutyCycleType_Lab"        , input.DutyCycleType_Lab;
        "DrivCycle_MotorLAB"       , input.DrivCycle_MotorLAB;
        "LabThermalCoupling_DutyCycle", input.LabThermalCoupling_DutyCycle;
        "Mass_MotorLAB"            , input.Mass_MotorLAB;
        "K_r_MotorLAB"             , input.K_r_MotorLAB;
        "rho_MotorLAB"             , input.rho_MotorLAB;
        "B_cont_MotorLAB"          , input.B_cont_MotorLAB;
        "A_f_MotorLAB"             , input.A_f_MotorLAB;
        "C_d_MotorLAB"             , input.C_d_MotorLAB;
        % input.N_d_MotorLAB        , [];
        "TorqueCapTrue_MotorLAB"   , input.TorqueCapTrue_MotorLAB;
        % input.TorqueCap_MotorLAB , [];
        "R_w_MotorLAB"             , input.R_w_MotorLAB;
        "WheelInertia"             , input.WheelInertia;
        "M_o_MotorLAB"             , input.M_o_MotorLAB;
        "T_cont_MotorLAB"          , input.T_cont_MotorLAB;
        "SpeedCapTrue_MotorLAB"    , input.SpeedCapTrue_MotorLAB;
        % input.SpeedCap_MotorLAB , [];
    };
    
    % 조건에 따라 필드 추가
    if input.LabThermalCoupling_DutyCycle == 2
        data = [data; {"Transient_Number_Cycles", input.Transient_Number_Cycles}];
    end
    if input.TorqueCapTrue_MotorLAB || input.TorqueCapTrue_MotorLAB == 1
        data = [data; {"TorqueCap_MotorLAB", input.TorqueCap_MotorLAB}];
    end
    if input.SpeedCapTrue_MotorLAB || input.SpeedCapTrue_MotorLAB == 1
        data = [data; {"SpeedCap_MotorLAB", input.SpeedCap_MotorLAB}];
    end
    
    % 테이블을 생성하고 반환
    settingTable = cell2table(data, 'VariableNames', {'AutomationName', 'CurrentValue'})
end