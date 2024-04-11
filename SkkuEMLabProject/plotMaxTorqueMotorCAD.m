function  [speedArray, BorderTorque]=plotMaxTorqueMotorCAD(matdata,onlyMaxLine)
    %% 데이터 로드
    if ischar(matdata)&&contains(matdata,'.mat')
    matdata       =            load(matdata)                ; % MAT 파일 로드
    elseif isstruct(matdata)
        matdata=matdata;
    end

    if nargin>1
    widthPlot=width(matdata.Speed);
    startline=widthPlot;
    else
    startline=1;
    widthPlot=width(matdata.Speed);
    end
    %% 각 속도에서의 최대 토크값 계산
    for machineMode=startline:widthPlot
        speedArray=replaceSimilarData(matdata.Speed(:,machineMode));
        torqueArray=replaceSimilarData(matdata.Shaft_Torque(:,machineMode));    
        [speedArray, BorderTorque] = plotMaxTorque(speedArray, torqueArray);
        
        %% Power and Torque Limit Array
        powerCalcArray=calcPowerArray(speedArray,torqueArray);
        powerLimitArray=min(powerCalcArray,360);
        TorqueLimitArray=calInvPowerArray(speedArray,powerLimitArray);
        
        %% Plot
        % plotMaxTorque(speedArray,TorqueLimitArray)
        hold on
    
        % Setting
        formatter_sci
        a=gca;
        a.XLabel.String='Speed[RPM]';
        a.YLabel.String='Torque[Nm]';
        % if machineMode==width(matdata.Speed)
        %  plot(speedArray,TorqueLimitArray,'LineWidth',2)
        % end
        hold on
     end
    % xlabel('Speed, RPM');
    % ylabel('Torque, N*m');
    % title('Max Torque vs. Speed');
end