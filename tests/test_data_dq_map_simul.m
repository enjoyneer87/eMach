%  init

% object make
HDEVdata=DataDqMap(8);

ee_ece_table % maxwell

PmsmFem.NumPolePairs = HDEVdata.p/2;
PmsmFem.idVec_A = idVec; % Direct-asis current vector, iD
PmsmFem.iqVec_A = iqVec; % Quadrature-axis current vector, iQ
PmsmFem.angleVec_deg = angleVec; % Rotor angle vector, theta
PmsmFem.fluxD_Wb = fluxD; % D-axis flux linkage, Fd(iD,iQ,theta)
PmsmFem.fluxQ_Wb = fluxQ; % Q-axis flux linkage, Fq(iD,iQ,theta)
PmsmFem.torque_Nm = torque; % Torque matrix, T(iD,iQ,theta)
clear N idVec iqVec angleVec fluxD fluxQ torque flux0
PmsmFem.Rs_Ohm = 0.07; % Stator resistance per phase, Rs

%% Iron Losses

PmsmFem.openCircuitLossVec_W = [80 25 5];
PmsmFem.shortCircuitLossVec_W = [230 55 10];
PmsmFem.frequencyForLosses_Hz = 150;
PmsmFem.shortCircuitCurrent_A = 85;

%% Mechanical

PmsmFem.rotorInertia_kg_m2 = 3.93*0.01^2; % Rotor inertia
PmsmFem.rotorDamping_Nm_per_radps = 0;  % Rotor damping

%% Variables

PmsmFem.initialDAxisCurrent_A = 0;
PmsmFem.initialQAxisCurrent_A = 0;
PmsmFem.initialRotorSpeed_rpm = 0;
PmsmFem.initialRotorAngle_rad = -pi/2/PmsmFem.NumPolePairs;



%% to check

% HDEVdata.rpm=rpm;
HDEVdata.current_dq_map.id=PmsmFem.idVec_A;
HDEVdata.current_dq_map.iq=PmsmFem.iqVec_A;
HDEVdata.flux_linkage_map.in_d=PmsmFem.fluxD_Wb 
HDEVdata.flux_linkage_map.in_q=PmsmFem.fluxQ_Wb 
HDEVdata.angleVec = PmsmFem.angleVec_deg; % Rotor angle vector, theta

HDEVdata.Rs=PmsmFem.Rs_Ohm ;

% HDEVdata.current_dq.Iq
% preconditionss
%2d style
% 
HDEVdata.plot_xdyq(HDEVdata,'flux')
% HDEVdata.plot_xdyq(HDEVdata)
% 
% HDEVdata.plot_xdyq(HDEVdata,'voltage')
% HDEVdata.plot_xdyq(HDEVdata,'torque')



%3d style

