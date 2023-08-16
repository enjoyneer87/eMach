function basePointInfo = findMaxTorqueRPM(motorCurve)
    % Find the maximum torque value
    max_torque = max(motorCurve.motor_max_t);

    % Define the tolerance as 0.2% of the maximum torque
    tolerance = 0.002 * max_torque;

    % Find the indices corresponding to the torque values within the tolerance
    idx = find(abs(motorCurve.motor_max_t - max_torque) <= tolerance);

    % Retrieve all corresponding RPM values
    basePointInfo.maxTorque         = motorCurve.motor_max_t(idx);
    basePointInfo.maxTorqueRPM      = motorCurve.rpm(idx);
    basePointInfo.kW                = motorCurve.motor_max_kW(idx);
    basePointInfo.basePointkW       = max(basePointInfo.kW);
    basePointInfo.basePointRPM      = max(basePointInfo.maxTorqueRPM);
    basePointInfo.basePointTorque   = max_torque;
end
