function plotVehiclePerformance(vehiclePerformData)
    % Create a new figure
    figure(10);
    % Plot the power vs. speed curve (left y-axis)
    yyaxis left;
    plot(vehiclePerformData.speed_kph, vehiclePerformData.force_newtons, 'LineWidth', 2);
    xlabel('Speed (kph)');
    ylabel('Force (N)');
    grid on;

    % Create a second y-axis for the force scale
    yyaxis right;
    plot(vehiclePerformData.speed_kph, vehiclePerformData.power_kw, 'LineWidth', 2);
    ylabel('Power (kW)');

    % Set the right y-axis color to match the force curve
    ax = gca;
    ax.YAxis(2).Color = 'k';

    % Title and legend
    title('Power and Force vs. Speed');
    legend('Force', 'Power');
    formatter_sci
end