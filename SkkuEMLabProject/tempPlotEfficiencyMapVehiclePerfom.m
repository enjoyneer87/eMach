function tempPlotEfficiencyMapVehiclePerfom(caseNum,DoEStruct,vehicleData,BasePointOutput,vehiclePerformData)
%% Plot 
% Plot]모터 Curve와 모터 요구사양(차량) Curve 
    vehicleData.N_d_MotorLAB=DoEStruct.DoEInputTable.N_d_MotorLAB(caseNum,:);  %[TC] 범용성 증가 필요
    calcVehicleLateralDynamics(vehicleData,vehiclePerformData);                %[TC] 변수 변경필요
% 모터 해석 Curve
    matFilePath=BasePointOutput.matFilePath;
    % 효율맵
    figure(6)
    MatFileData=plotEfficiencyMotorcad(matFilePath);
    legend('hide'); % 범례 숨기기

    figure(6)
    [speedArray,BorderTorque]=plotMaxTorqueMotorCAD(MatFileData);  % 기존 코드는 전류별 plotTNperAmpMCAD()
    % figure(6)
    % plot(speedArray,BorderTorque)
    % [TC]PN plot
    figure(7)
    plotPowerCurveMCAD(MatFileData); % MaxCurve 기능도 같이 포함

    %[TB] % plotMaxPowerCurveMCAD(MatFileData)
end