function data = fcnCorrectShaftTorque(data)
% INPUT:
% - data: struct containing electromagnetic torque (T_E [Nm]), 
% losses (P [W]), 
% and RPM

% OUTPUT:
% - out: struct containing corrected shaft torque (T_S [Nm])

% Calculate shaft torque (T_S [Nm])
% T_S = data.Electromagnetic_Torque - (data.Iron_Loss+data.Stator_Copper_Loss_AC+data.Magnet_Loss+data.)./ ((2*pi/60) .* data.Speed);
T_S = data.Electromagnetic_Torque - (1.1*data.Total_Loss-data.Stator_Copper_Loss_DC)./ ((2*pi/60) .* data.Speed);

% Output corrected shaft torque (T_S [Nm])
% out = struct('T_S', T_S);
data.T_S = T_S;
end