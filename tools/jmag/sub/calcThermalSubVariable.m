
TC_air = 0.02;
HTC_air = 10;



%% fluid 
flow_velocity = pi * (rotor_radius * 2 / 1000) * rotor_speed * 60;


%% Shaft
V_shaft = (shaft_length / 1000) * (pi * (shaft_diameter / 2 / 1000)^2);

R_shaft = (1 / shaft_conductivity) * (shaft_length / 1000) / (pi * (shaft_diameter / 2)^2 / 1000000);
C_shaft = shaft_specific_heat * shaft_density * V_shaft;

%% Housing Dimension
Housing_height = housing_height;
Housing_outer_radius = housing_outer_diameter / 2;
Housing_inner_radius = housing_inner_diameter / 2;

%% Axial Resistance
R_housing_axial = (1 / housing_conductivity) * (housing_height / 1000) / (pi * (housing_outer_diameter / 2 / 1000)^2 - pi * (housing_inner_diameter / 2 / 1000)^2);

%% % Housing Heat Capacity
% Housing Volume
% V_housing = (((pi * (housing_outer_diameter / 2)^2 - pi * (housing_inner_diameter / 2)^2) * housing_height) + (pi * (housing_outer_diameter / 2)^2) * (housing_outer_diameter - housing_inner_diameter)) / 1000000000;
V_housing  = calcHousingVolume(housing_outer_diameter*scaleFactor, housing_inner_diameter, housing_height)
% C_housing  = calcHeatCapHousing(housing_density,housing_specific_heat,V_housing)
C_housing = housing_density * housing_specific_heat * V_housing;

%% Housing Side Convection Natural
A_housing=calcCylinderSideArea(housing_height,housing_outer_diameter);
R_housing_to_ambient = 1 / HTC_air / A_housing;
% A_housing = housing_height * housing_outer_diameter * pi / 1000000;
