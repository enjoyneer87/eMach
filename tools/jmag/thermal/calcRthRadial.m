function R = calcRthRadial(C_F, k, L, outerR, innerR)
    % Calculate the radial thermal resistance of a cylindrical structure.
    %
    % Parameters:
    % C_F: Correction factor
    % k: Thermal conductivity of the material (W/m/°C)
    % L: Length of the cylinder (mm)
    % r1: Inner radius of the cylinder (mm)
    % r2: Outer radius of the cylinder (mm)
    %
    % Returns:
    % R: Radial thermal resistance (°C/W)
    LinMeter    =mm2m(L);
    r1inMeter   =mm2m(innerR);
    r2inMeter   =mm2m(outerR);

    % Calculate the radial thermal resistance
    R = C_F * (1 / (2 * pi * k * LinMeter)) * log(r2inMeter / r1inMeter);
end
