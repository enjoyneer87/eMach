function R = calcRthWaterJacket(C_F, h, r, W, N)
    % Calculate the thermal resistance of a water jacket.
    %
    % Parameters:
    % C_F: Correction factor (Default: 1)
    % h: Heat transfer coefficient (W/m²/°C)
    % r: Radius of the cooling target (mm)
    % W: Width of the cooling target (mm)
    % N: Number of thermal resistor components
    %
    % Returns:
    % R: Thermal resistance value (°C/W)

    % Calculate the area
    A = 2 * pi * r * W * N;  % Area in mm²

    % Convert A from mm² to m²
    A_m2 = A / (1000 * 1000);  % Convert mm² to m²

    % Calculate thermal resistance
    R = C_F * (1 / (h * A_m2));
end
