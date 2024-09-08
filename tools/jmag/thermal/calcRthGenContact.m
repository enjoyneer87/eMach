function R = calcRthGenContact(C_F, l, k, A)
% Calculate the thermal resistance value.
% Parameters: C_F: Correction factor (Default: 1) 
% l: Distance between parts (mm) 
% k: Thermal conductivity between parts (W/m/°C) 
% A: Contact surface area (mm²)
% Returns: R: Thermal resistance value (°C/W)
    % Convert l and A from mm to m for the formula
    l_m = l / 1000;  % Convert mm to m
    A_m2 = A / (1000 * 1000);  % Convert mm² to m²

    % Calculate thermal resistance
    R = C_F * (l_m / (k * A_m2));  %degC/W
    
end
%% 
% Thermal Resistance
% 
% $$R=C_F \times \frac{l}{k \times A}$$           $$R$ : Thermal resistance 
% value (deg $\mathrm{C} / \mathrm{W})$$k$ : Thermal conductivity of the object 
% to be heated/cooled $(\mathrm{W} / \mathrm{m} / \mathrm{deg}$C)$l$ : Length 
% of the object to be heated/cooled $(\mathrm{mm})$$A$ : Area of the surface receiving 
% heat $\left(\mathrm{mm}^{\wedge} 2\right)$$C_F$ : Correction factor (Default: 
% 1 )$
% 
% General Contact = 
% 
% 고정자 코어와 하우징 또는 자석과 코어 등과 같은 부품 간의 접촉으로 인해 발생하는 열 저항 값은 열 회로 계산에서 고려됩니다.
% 
% $$R=C_F \times \frac{l}{k \times A}$$        $$R$ : Thermal resistance value 
% ( $\mathrm{deg} \mathrm{C} / \mathrm{W}$ )$C_F$ : Correction factor (Default: 
% 1)$l$ : Distance between parts $(\mathrm{mm})$$k$ : Thermal conductivity between 
% parts $(\mathrm{W} / \mathrm{m} / \mathrm{deg} \mathrm{C})$$A$ : Contact surface 
% area $\left(\mathrm{mm}^{\wedge} 2\right)$[Good Fit $(0.01 \mathrm{~mm})]$[Bad 
% Fit $(0.1 \mathrm{~mm})]$$
% 
% same as thermal resistance
% 
%