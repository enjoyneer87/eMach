function  [speedArray, BorderTorque]=plotMaxTorqueMotorCAD(matdata)
    % 각 속도에서의 최대 토크값 계산
    for machineMode=1:width(matdata.Speed)
    speedArray=replaceSimilarData(matdata.Speed(:,machineMode));
    torqueArray=replaceSimilarData(matdata.Shaft_Torque(:,machineMode));
    
    [speedArray, BorderTorque] = plotMaxTorque(speedArray, torqueArray);

    powerCalcArray=calcPowerArray(speedArray,torqueArray);
    powerLimitArray=min(powerCalcArray,240)
    TorqueLimitArray=calInvPowerArray(speedArray,powerLimitArray)
    
    plotMaxTorque(speedArray,TorqueLimitArray)
    hold on
    formatter_sci
    a=gca
    a.XLabel.String='Speed[RPM]';
    a.YLabel.String='Torque[Nm]';
    hold on
    end
    % xlabel('Speed, RPM');
    % ylabel('Torque, N*m');
    % title('Max Torque vs. Speed');
end