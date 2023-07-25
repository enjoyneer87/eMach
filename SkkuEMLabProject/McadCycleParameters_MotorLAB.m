function variable=McadCycleParameters_MotorLAB()
    variable = struct();     
    variable.Wheellnertia                  =[];  
    variable.DCExtDataType_Lab             =[];      
    variable.DrivCycle_MotorLAB            =[];      
    variable.Mass_MotorLAB                 =[];  %   vehicle mass
    variable.A_f_MotorLAB                  =[];  %   Frontal area
    variable.R_w_MotorLAB                  =[];  %   Wheel radius
    variable.K_r_MotorLAB                  =[];  %   Rolling resistance coefficient
    variable.C_d_MotorLAB                  =[];  %   Drag coefficient
    variable.M_o_MotorLAB                  =[];  %   Mass correction factor
    variable.rho_MotorLAB                  =[];  %   Air density
    variable.N_d_MotorLAB                  =[];  %   Gear ratio (final drive ratio) in the vehicle model
    variable.T_cont_MotorLAB               =[];  
    variable.B_cont_MotorLAB               =[];  
    %                   
    variable.DutyCycleType_Lab             =[];     
    variable.DrivCycle_MotorLAB            =[];     

end