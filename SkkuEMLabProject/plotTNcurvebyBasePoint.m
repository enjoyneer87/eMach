function [baseTorque,maxSpeedTorque]=plotTNcurvebyBasePoint(baserpm, maxrpm, kW)

    fontsize=18;
    rpm = 100:100:maxrpm;  % RPM 범위 설정
    rpm_radsec = rpm2radsec(rpm);  % RPM을 라디안/초로 환산
    baseRadesec = rpm2radsec(baserpm);
    baseTorque = kW / baseRadesec * 1000;
    torque = [baseTorque * ones(1, sum(rpm <= baserpm)), kW * 1000 ./ rpm_radsec(rpm > baserpm)];  % 토크 계산
    maxSpeedTorque=kW * 1000 / (maxrpm * (2 * pi / 60));
    % figure('Position', [100, 100, 1200, 600]);  % 너비 800, 높이 600으로 고정

    [h(1)]=plot(rpm, torque, 'b', 'LineWidth', 2);  % 그래프 그리기
    title('TN Curve');
    grid on;
    
    set(gca, 'FontName', 'Times New Roman');  % 폰트 설정
    
    xlabel('Speed [RPM]');
    ylabel('Torque [Nm]');
    
    hold on;  % 그래프 유지

    % baserpm과 해당 토크에 점과 텍스트 추가
    [h(2)]=scatter(baserpm, baseTorque, 'filled','ro');
    % text(baserpm, baseTorque, sprintf('%.2f Nm @ %d RPM', baseTorque, baserpm), 'VerticalAlignment', 'bottom', 'FontName', 'Times New Roman','FontSize', fontsize);
    
    % maxrpm과 해당 토크에 점과 텍스트 추가
    [h(3)]=scatter(maxrpm, kW * 1000 / (maxrpm * (2 * pi / 60)),'filled', 'go');
    % text(maxrpm, kW * 1000 / (maxrpm * (2 * pi / 60)), sprintf('%.2f Nm @ %d RPM', kW * 1000 / (maxrpm * (2 * pi / 60)), maxrpm), 'VerticalAlignment', 'bottom','Position',[maxrpm-0.35*maxrpm,kW * 1000 / (maxrpm * (2 * pi / 60))] ,'FontName', 'Times New Roman','FontSize', fontsize);

    ylim([0, max(torque)*1.2]);
    % legend('EfficiencyMap')
    % legend(h(1))
    formatter_sci()
    hold off;  % 그래프 종료


end

