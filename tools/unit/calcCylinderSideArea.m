function A_housing=calcCylinderSideArea(housing_height,housing_outer_diameter)
% housing_height [mm]
% housing_outer_diameter [mm]
A_housing = housing_height * housing_outer_diameter * pi / 1e6; % [m]

end