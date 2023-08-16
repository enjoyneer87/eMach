function smallPoint=decideSimulationTargetPoint(newMotorCurve,motorRequiredCurve)   
    %% Find Base Point and Max Point
    basePoint                       = findMaxTorqueRPM(newMotorCurve);
    MaxRPMPointInfo                 = findMaxRPMTorque(newMotorCurve);
    % check
    % if height(motorCurve)==height(motorRequiredCurve.power_kw)
    motorRequiredCurve.power_kw =motorRequiredCurve.motor_max_kW;
    motorRequiredCurve.torqueConv   = power2torque(motorRequiredCurve.power_kw,newMotorCurve.rpm);
    motorRequiredCurve.motor_max_kW=motorRequiredCurve.power_kw;
    
    %% Interpolate 
    %% 작은게 무조건
    % smallPoint 
    % Find the index for basePointRPM in motorCurve.rpm
    idx_base = find(newMotorCurve.rpm == basePoint.basePointRPM, 1);
    % Compare and store the smaller value for base point torque
    smallPoint.basePointRPM     = basePoint.basePointRPM;
    smallPoint.basePointkW      = min(basePoint.basePointkW, motorRequiredCurve.power_kw(idx_base));
    smallPoint.basePointTorque  = min(basePoint.basePointTorque, motorRequiredCurve.torqueConv(idx_base));
    
    % Find the index for MaxRPM in motorCurve.rpm
    idx_max = find(newMotorCurve.rpm == MaxRPMPointInfo.MaxRPM, 1);
    % Compare and store the smaller value for max RPM point torque
    smallPoint.MaxRPM           = MaxRPMPointInfo.MaxRPM;
    smallPoint.kWAtMaxRPM       = min(MaxRPMPointInfo.kWAtMaxRPM, motorRequiredCurve.power_kw(idx_max));
    smallPoint.TorqueAtMaxRPM   = min(MaxRPMPointInfo.TorqueAtMaxRPM, motorRequiredCurve.torqueConv(idx_max));
    
    %
    smallPoint.MaxkW        = max(max(newMotorCurve.motor_max_kW),max(motorRequiredCurve.motor_max_kW));
    smallPoint.MaxTorque    = max(max(newMotorCurve.motor_max_t),max(motorRequiredCurve.motor_max_t));
    %% PN Curve
    figure(7)
    plot(newMotorCurve.rpm,newMotorCurve.motor_max_kW,'DisplayName','DesignedMotorCurve')
    hold on
    scatter(basePoint.basePointRPM,basePoint.basePointkW,'HandleVisibility', 'off');
    scatter(MaxRPMPointInfo.MaxRPM,MaxRPMPointInfo.kWAtMaxRPM,'HandleVisibility', 'off');
    legend
    plot(newMotorCurve.rpm,motorRequiredCurve.power_kw,'DisplayName','RequireMotorCurve')
    scatter(smallPoint.MaxRPM,smallPoint.kWAtMaxRPM,'x','HandleVisibility', 'off');
    scatter(smallPoint.basePointRPM,smallPoint.basePointkW,'x','HandleVisibility', 'off');
   
    %% TN Curve
    figure(6)
    plot(newMotorCurve.rpm,newMotorCurve.motor_max_t,'DisplayName','DesignedMotorCurve')
    hold on
    scatter(basePoint.basePointRPM,basePoint.basePointTorque)
    scatter(MaxRPMPointInfo.MaxRPM,MaxRPMPointInfo.TorqueAtMaxRPM)   
    plot(newMotorCurve.rpm,motorRequiredCurve.torqueConv,'DisplayName','RequireMotorCurve');
    scatter(smallPoint.MaxRPM,smallPoint.TorqueAtMaxRPM,'x');
    scatter(smallPoint.basePointRPM,smallPoint.basePointTorque,'x');    
end
