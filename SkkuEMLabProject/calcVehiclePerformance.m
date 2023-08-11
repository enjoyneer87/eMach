function vehiclePerformData = calcVehiclePerformance(vehiclePowerCurve)
    % maximum_hp = 1019;

    % Define the speed range from 0 to 200 mph
    % speed_mph = 0:200;
    speed_mph = vehiclePowerCurve.speed_mph;

    % Define the power curve in HP
    power_hp = vehiclePowerCurve.power_hp;

    %% Smoothing
    % ... (Smoothing code remains commented out)

    % Convert speed from mph to kph
    speed_kph = speed_mph * 1.60934;

    % Convert power to kW
    power_kw = power_hp * 0.7457;

    % Convert power to force
    power_watts = power_hp * 745.7;
    force_newtons = power_watts ./ (speed_kph * 1000 / 3600);

    % Store the results in a struct
    vehiclePerformData = struct();
    vehiclePerformData.speed_kph = speed_kph;
    vehiclePerformData.power_kw = power_kw;
    vehiclePerformData.force_newtons = force_newtons;
end