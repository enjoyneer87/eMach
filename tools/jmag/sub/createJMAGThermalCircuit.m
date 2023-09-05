app.SetCurrentStudy('rotor');
rotorModel = app.GetModel('rotor-Case1');
rotorStudy = rotorModel.GetStudy('rotor');
rotorCircuit = rotorStudy.CreateCircuit();

components = {
    "Gap", "R_contact_core_housing", "R_shaft", "R_housing_up", "R_housing_axial", ...
    "Upper_core_surface_to_air", "R_water_jacket", "R_housing_radial", "Lower_core_surface_to_air", ...
    "R_coilend_to_air2", "Upper_core_surface_to_air", "Lower_core_surface_to_air", "R_shaft_copy", ...
    "R_to_air", "Ambient", "C_shaft", "C_housing", "R_housing_low", "WJ_inlet_temp", "Control"
};

for i = 1:numel(components)
    rotorCircuit.CreateComponent("ThermalResistor", components{i});
end

positions = {
    [-102, 44], [-102, 17], [-99, -68], [-91, -66], [-89, -71], ...
    [-102, 32], [-100, 23], [-102, 25], [-102, 1], [-102, 1], ...
    [-66, -61], [-66, -72], [-99, -72], [-100, 27], [-98, 25], ...
    [-97, -70], [-104, 27], [-91, -76], [-98, 21], [-119, 44]
};

for i = 1:numel(components)
    rotorCircuit.CreateInstance(components{i}, positions{i}(1), positions{i}(2));
end

wirePositions = {
    [-95, -76, -93, -76], [-95, -66, -93, -66], [-89, -66, -89, -69], [-89, -73, -89, -76], ...
    [-102, 34, -108, -60], [-108, -60, -89, -61], [-89, -65, -89, -66], [-102, 3, -116, -81], ...
    [-116, -81, -89, -76], [-122, -12, -100, -12], [-100, -39, -129, -81], [-116, -81, -129, -81], ...
    [-66, -59, -89, -61], [-89, -61, -89, -65], [-66, -70, -84, -75], [-89, -76, -84, -75], ...
    [-99, -74, -99, -76], [-99, -70, -106, -70], [-122, -12, -108, -60], [-95, -66, -99, -66], ...
    [-99, -76, -95, -76], [-106, -70, -106, -85], [-102, 23, -102, 19]
};

for i = 1:numel(wirePositions)
    rotorCircuit.CreateWire(wirePositions{i}(1), wirePositions{i}(2), wirePositions{i}(3), wirePositions{i}(4));
end