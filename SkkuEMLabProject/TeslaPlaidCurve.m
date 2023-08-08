% maximum_hp =1019; 

% Define the speed range from 0 to 200 mph
% speed_mph = 0:200;
speed_mph = (TeslaPowerCurve.spped_mph);



% Define the power curve in HP
% power_hp = zeros(size(speed_mph));
% power_hp(speed_mph <= 60) = maximum_hp * speed_mph(speed_mph <= 60) / 60;
% power_hp(speed_mph > 60 & speed_mph <= 200) = maximum_hp;
power_hp = (TeslaPowerCurve.power_hp);


%% Smoothing

% new_speed = linspace(0, 200, 200); % 100개의 등간격 속도 포인트 생성

% [smoothed_power,interpolated_power]=interpolateSmoothCurve(speed_mph,power_hp,new_speed);
% power_hp= interpolated_power;
% speed_mph = new_speed;
%%

% Convert speed from mph to kph
speed_kph = speed_mph * 1.60934;

% Convert power to kW
power_kw = power_hp * 0.7457;

% Convert power to force
% 1 horsepower (HP) is approximately equal to 745.7 watts
power_watts = power_hp * 745.7;
force_newtons = power_watts ./ (speed_kph * 1000 / 3600); % Convert kph to m/s

% Create a new figure
figure(10);

% Plot the power vs. speed curve (left y-axis)
yyaxis left;
plot(speed_kph, force_newtons, 'LineWidth', 2);
xlabel('Speed (kph)');
ylabel('Force (N)');

grid on;

% Create a second y-axis for the force scale
yyaxis right;
plot(speed_kph, power_kw, 'LineWidth', 2);
ylabel('Power (kW)');

% Set the right y-axis color to match the force curve
ax = gca;
ax.YAxis(2).Color = 'k';

% Title and legend
title('Power and Force vs. Speed');
legend('Force', 'Power');

formatter_sci

vehiclePerformData=struct();
vehiclePerformData.speed_kph=speed_kph;
vehiclePerformData.power_kw=power_kw;
vehiclePerformData.force_newtons=force_newtons;

