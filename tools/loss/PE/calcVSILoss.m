function [ConductionLoss,SwitchingLoss]=calcVSILoss(V_DC, f_sw, hat_is, theta, m1,PowerModuleDataStruct)
% Calculate the loss of the VSI
%% Input description
% V_DC: DC link voltage
% f_sw: switching frequency
% hat_is: RMS value of the stator current
% theta: angle Between stator current and voltage
% m1: modulation index

if nargin < 6
%% 소자 데이터 시트에서 확인필요
% derived Variable
% I_cn = 1.092 * I_em_rms - 6.05;    % the range of values of nominal collector current 50-800A [16]
I_cn = 800 ;
I_ref = 400;
% Define given variables
Vt_IGBT = 0.695;                  % V % On-state threshold voltage for IGBT
Vt_diode = 0.797;                 % V % On-state threshold voltage for diode
% derived Variable
Ron_IGBT = mm2m(990.07 * I_cn^(-1.003) ); % Ohm      % On-state resistance for IGBT 
Ron_diode = mm2m(675.61 * I_cn^(-1.004)); % Ohm     % On-state resistance for diode  
K_i_igbt    =0.6;
K_i_diode   = 0.6;
% given variable
Kv_IGBT     = 1.35;       % Voltage dependency exponent for IGBT
Kv_diode    = 0.6;       % Voltage dependency exponent for diode
% derived Variable
E_onIGBT    = 9.964e-6 .* hat_is.^2 + 0.0156 .* hat_is + 0.6221; % mJ
E_offIGBT   = 2.4259e-8 .* hat_is.^3 - 5.7183e-6 .* hat_is.^2 + 0.0357 .* hat_is + 1.8700; % mJ    % Energy dissipation for IGBT on/off in Joules                          
E_diode     = 2.8029e-6 .* hat_is.^2 + 0.0139 .* hat_is + 0.9973; % mJ                          % Energy dissipation for diode off in Joules  
m3          = m1 / 6;             % Third harmonic injection modulation index
else 
    % I_cn = PowerModuleDataStruct.I_cn;
    I_ref = PowerModuleDataStruct.I_ref;
    Vt_IGBT = PowerModuleDataStruct.Vt_IGBT;
    Vt_diode = PowerModuleDataStruct.Vt_diode;
    Ron_IGBT = PowerModuleDataStruct.Ron_IGBT;
    Ron_diode = PowerModuleDataStruct.Ron_diode;
    Kv_IGBT = PowerModuleDataStruct.Kv_IGBT;
    Kv_diode = PowerModuleDataStruct.Kv_diode;
    E_onIGBT = PowerModuleDataStruct.E_onIGBT;
    E_offIGBT = PowerModuleDataStruct.E_offIGBT;
    E_diode = PowerModuleDataStruct.E_diode;
    m3 = PowerModuleDataStruct.m3;
    K_i_igbt = PowerModuleDataStruct.K_i_igbt;
    K_i_diode = PowerModuleDataStruct.K_i_diode;
end

%% Conduction Loss
P_cond_IGBT = 6.*((1./(2.*pi) + m1.*cos(theta)./8).*Vt_IGBT.*hat_is + ...
    (1./8 + m1.*cos(theta)./(3.*pi) - m3.*cos(3.*theta)./(15.*pi)).*Ron_IGBT.*hat_is.^2);
P_cond_diode = 6.*((1./(2.*pi) - m1.*cos(theta)./8).*Vt_diode.*hat_is + ...
    (1./8 - m1.*cos(theta)./(3.*pi) + m3.*cos(3.*theta)./(15.*pi)).*Ron_diode.*hat_is.^2);

%%  Switching Loss
P_sw_IGBT = (f_sw/pi) .* (E_onIGBT + E_offIGBT) .* ((hat_is)./I_ref).^K_i_igbt .* ((V_DC/300).^Kv_IGBT);
P_sw_diode = (f_sw/pi) .* E_diode .* ((hat_is)./I_ref).^K_i_diode .* ((V_DC/300).^Kv_diode);

ConductionLoss.P_cond_IGBT = P_cond_IGBT;
ConductionLoss.P_cond_diode = P_cond_diode;

SwitchingLoss.P_sw_IGBT = P_sw_IGBT/1000;
SwitchingLoss.P_sw_diode = P_sw_diode/1000;

end