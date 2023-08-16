% maximum_hp =1019; 
load("TeslaSPlaidPowerCurveDigitizer.mat");   % TeslaPowerCurve Define
load("TeslaSPlaid.mat")

% Define the speed range from 0 to 200 mph
% speed_mph = 0:200;
speed_mph = (TeslaPowerCurve.speed_mph);



% Define the power curve in HP
% power_hp = zeros(size(speed_mph));
% power_hp(speed_mph <= 60) = maximum_hp * speed_mph(speed_mph <= 60) / 60;
% power_hp(speed_mph > 60 & speed_mph <= 200) = maximum_hp;
power_hp = (TeslaPowerCurve.power_hp)*correctionFactor;


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
force_newtons = watt2Force(power_watts, speed_kph);


load("linearForceNewtons.mat")
linearForceNewtons=linearForceNewtons*correctionFactor;

%% Power
power_watts                 =force2Watt(linearForceNewtons,speed_kph);
power_kw=power_watts/1000;
power_hp                    =kw2hp(power_kw);
% Force
force_newtons               =watt2Force(power_watts, speed_kph);

% Speed
speed_mph                   =kph2mph(speed_kph);
speed_ms                    =kph2ms(speed_kph);
%%
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

TeslaPowerCurve=table(speed_ms,speed_mph,speed_kph,power_hp,power_kw,power_watts,force_newtons);

vehiclePerformData=struct();
vehiclePerformData.speed_kph=speed_kph;
vehiclePerformData.power_kw=power_kw;
vehiclePerformData.force_newtons=force_newtons;

clear("speed_ms","speed_mph","speed_kph","power_hp","power_kw","power_watts","force_newtons","linearForceNewtons")
