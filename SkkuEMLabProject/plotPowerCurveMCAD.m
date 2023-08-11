function  [speedArray, BorderTorque]=plotPowerCurveMCAD(matdata)
    %% 각 속도에서의 최대 토크값 계산
    for machineMode=1:width(matdata.Speed)
    speedArray=replaceSimilarData(matdata.Speed(:,machineMode));
    torqueArray=replaceSimilarData(matdata.Shaft_Torque(:,machineMode));    
    % [speedArray, BorderTorque] = plotMaxTorque(speedArray, torqueArray);
    
    %% Power and Torque Limit Array
    powerCalcArray          =calcPowerArray(speedArray,torqueArray);
    powerLimitArray         =min(powerCalcArray,360);
    TorqueLimitArray        =calInvPowerArray(speedArray,powerLimitArray);
    
    %% Plot
    % plotMaxTorque(speedArray,TorqueLimitArray)
    plotMaxTorque(speedArray,powerCalcArray);
    hold on
    % Setting
    formatter_sci

    hold on
    if machineMode==width(matdata.Speed) % 최대 전류만 plot
    plot(speedArray,powerLimitArray,'LineWidth',2);
    end
    a=gca;
    a.XLabel.String='Speed[RPM]';
    a.YLabel.String='Power[kW]';
    end
    % xlabel('Speed, RPM');
    % ylabel('Torque, N*m');
    % title('Max Torque vs. Speed');
end