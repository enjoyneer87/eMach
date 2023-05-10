testCalcShaftTorque


%% BackUp From Calc_manual_shaft_torque 
Post_Cal_Loss=iron_loss;

% Post_Cal_Loss = K_Mech*(Mech_Loss)+K_Hys*(Hysteresis_loss)+ K_Core_Eddy*(Eddy_loss)+ K_AC_Copper*(AC_Copper_Loss)+K_AC_Magnet*(Magnet_Loss);
% P_mech = 2*pi*(Effy_Map(i,1)/60)*abs(torque) - Post_Cal_Loss;  % Wm * Torque   % Shaft 토크

P_mech = 2*pi*(1700/60)*abs(torque) - Post_Cal_Loss;  % Wm * Torque   % Shaft 토크
Shaft_Torque = P_mech/(2*pi*(Effy_Map(i,1)/60));



%% 