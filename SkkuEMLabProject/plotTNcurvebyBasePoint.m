function [baseTorque, maxSpeedTorque] = plotTNcurvebyBasePoint(baserpm, maxrpm, kW, plotType)
    fontsize = 18;
    rpm = 100:100:maxrpm;
    rpm_radsec = rpm2radsec(rpm);
    baseRadesec = rpm2radsec(baserpm);
    baseTorque = kW / baseRadesec * 1000;
    torque = [baseTorque * ones(1, sum(rpm <= baserpm)), kW * 1000 ./ rpm_radsec(rpm > baserpm)];
    maxSpeedTorque = kW * 1000 / (maxrpm * (2 * pi / 60));

    % Check if plotType is provided, otherwise, use 'b'
    if nargin < 4
        plotType = 'b';
    end

    [h(1)] = plot(rpm, torque, plotType, 'LineWidth', 2);  % Use plotType here
    title('TN Curve');
    grid on;

    set(gca, 'FontName', 'Times New Roman');
    xlabel('Speed [RPM]');
    ylabel('Torque [Nm]');

    hold on;

    [h(2)] = scatter(baserpm, baseTorque, 'filled', 'ro');
    text(baserpm, baseTorque, sprintf('%.2f Nm @ %d RPM', baseTorque, baserpm), 'VerticalAlignment', 'bottom', 'FontName', 'Times New Roman', 'FontSize', fontsize);
    legend('hide');
    [h(3)] = scatter(maxrpm, kW * 1000 / (maxrpm * (2 * pi / 60)), 'filled', 'go');
    text(maxrpm, kW * 1000 / (maxrpm * (2 * pi / 60)), sprintf('%.2f Nm @ %d RPM', kW * 1000 / (maxrpm * (2 * pi / 60)), maxrpm), 'VerticalAlignment', 'bottom', 'Position', [maxrpm - 0.35 * maxrpm, kW * 1000 / (maxrpm * (2 * pi / 60))], 'FontName', 'Times New Roman', 'FontSize', fontsize);
    legend('hide');
    ylim([0, max(torque) * 1.2]);
    legend('RequiredTN')
    formatter_sci()
    hold off;
end

