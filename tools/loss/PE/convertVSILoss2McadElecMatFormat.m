function elecMat=convertVSILoss2McadElecMatFormat(elecMatPath,f_sw,m1)
% elecMatPath='D:\KDH\Thesis\MCADDOE\M1_e10\e10_User\Lab\MotorLAB_elecdata.mat'
% Load the data
elecMat = load(elecMatPath);

%% Calculate the losses
f_sw_mat = repmat(f_sw,size(elecMat.Stator_Current_Phase_RMS)); % 3-phase system    
V_DC=elecMat.DC_Bus_Voltage     ;
theta=acos(elecMat.Power_Factor)        ;    % Power factor angle in radians
% m1   = 0.9; % modulation index 
m1_mat = repmat(m1,size(elecMat.Stator_Current_Phase_RMS)); % 3-phase system
[ConductionLoss,SwitchingLoss]=calcVSILoss(V_DC, f_sw_mat, elecMat.Stator_Current_Phase_RMS, theta, m1_mat);

%% Save the data
elecMat.P_cond_IGBT = ConductionLoss.P_cond_IGBT;
elecMat.P_cond_diode= ConductionLoss.P_cond_diode;
elecMat.P_sw_IGBT   = SwitchingLoss.P_sw_IGBT;
elecMat.P_sw_diode  = SwitchingLoss.P_sw_diode;
elecMat.P_cond      = ConductionLoss.P_cond_IGBT+ConductionLoss.P_cond_diode;
elecMat.P_sw        = SwitchingLoss.P_sw_IGBT+SwitchingLoss.P_sw_diode;
elecMat.P_diode    = ConductionLoss.P_cond_diode+SwitchingLoss.P_sw_diode;
elecMat.P_IGBT     = ConductionLoss.P_cond_IGBT+SwitchingLoss.P_sw_IGBT;
elecMat.P_VSI_total= elecMat.P_cond+elecMat.P_sw;


end