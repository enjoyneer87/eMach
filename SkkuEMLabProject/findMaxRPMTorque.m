function MaxRPMPointInfo = findMaxRPMTorque(motorCurve)
    % Find the index of the maximum RPM
    [max_rpm, idx] = max(motorCurve.rpm);

    % Retrieve the corresponding torque value
    max_torque = motorCurve.motor_max_t(idx);
    maxkW      = motorCurve.motor_max_kW(idx);

    % Create a structure to store the result
    MaxRPMPointInfo = struct('MaxRPM', max_rpm, 'TorqueAtMaxRPM', max_torque,'kWAtMaxRPM',maxkW);
end
