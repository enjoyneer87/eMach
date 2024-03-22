function ResultMotorcadEmagPhasorDiagram= motorcadResultPhasorDiagram(ResultMotorcadEmagPhasorDiagram)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here
% 1
% RmsBackEMFPhase
% mcad = actxserver('MotorCAD.AppAutomation');

[success,ResultMotorcadEmagPhasorDiagram.ShaftSpeed]=invoke(mcad,'GetVariable','ShaftSpeed');
[success,ResultMotorcadEmagPhasorDiagram.RMSBackEMFPhase] = invoke(mcad,'GetVariable','RmsBackEMFPhase');
% 2 The rms D axis Phase resistive Voltage
% RMSPhaseResistiveVoltage_D
[success,ResultMotorcadEmagPhasorDiagram.RMSPhaseResistiveVoltage_D] = invoke(mcad,'GetVariable','RMSPhaseResistiveVoltage_D');
% 3 The rms Q axis Phase resistive Voltage
% RMSPhaseResistiveVoltage_Q
[success,ResultMotorcadEmagPhasorDiagram.RMSPhaseResistiveVoltage_Q] = invoke(mcad,'GetVariable','RMSPhaseResistiveVoltage_Q');

% 4 The rms Phase resistive Voltage
% RMSPhaseResistiveVoltage
[success,ResultMotorcadEmagPhasorDiagram.RMSPhaseResistiveVoltage] = invoke(mcad,'GetVariable','RMSPhaseResistiveVoltage');

% 5 The reactive voltage drop D axis (Q axis current x Q axis inductance)
% RMSPhaseReactiveVoltage_D
[success,ResultMotorcadEmagPhasorDiagram.RMSPhaseReactiveVoltage_D] = invoke(mcad,'GetVariable','RMSPhaseReactiveVoltage_D');
% 6 The reactive voltage drop in Q axis (D axis current x D axis inductance)
% RMSPhaseReactiveVoltage_Q
[success,ResultMotorcadEmagPhasorDiagram.RMSPhaseReactiveVoltage_Q] = invoke(mcad,'GetVariable','RMSPhaseReactiveVoltage_Q');

% 7 The rms Phase Voltage at the terminals of the machine from phasor diagram
% PhasorRmsPhaseVoltage
[success,ResultMotorcadEmagPhasorDiagram.PhasorRMSPhaseVoltage] = invoke(mcad,'GetVariable','PhasorRmsPhaseVoltage');
% The required rms Phase Voltage at the output of the drive taking into account sine filter
% RmsPhaseDriveVoltage
% [success,ResultMotorcadEmagPhasorDiagram.RMSPhaseDriveVoltage] = invoke(mcad,'GetVariable','RmsPhaseDriveVoltage');

% 8 The rms Phase Voltage at the output of the supply
% PhaseVoltage
[success,ResultMotorcadEmagPhasorDiagram.PhaseVoltage] = invoke(mcad,'GetVariable','PhaseVoltage');

% 9  Load Angle from phasor diagram
% PhasorLoadAngle 
[success,ResultMotorcadEmagPhasorDiagram.PhasorLoadAngle] = invoke(mcad,'GetVariable','PhasorLoadAngle');

% 10 Power Factor Angle from phasor diagram
% PhasorPowerFactorAngle
[success,ResultMotorcadEmagPhasorDiagram.PhasorPowerFactorAngle] = invoke(mcad,'GetVariable','PhasorPowerFactorAngle');

% 11 The phase advance in electrical degrees
% PhaseAdvance
[success,ResultMotorcadEmagPhasorDiagram.PhaseAdvance] = invoke(mcad,'GetVariable','PhaseAdvance');

% 12 The calculated rms phase current
% RMSPhaseCurrent
[success,ResultMotorcadEmagPhasorDiagram.RMSPhaseCurrent] = invoke(mcad,'GetVariable','RMSPhaseCurrent');

% 13 
% RMSPhaseCurrent_D
[success,ResultMotorcadEmagPhasorDiagram.RMSPhaseCurrent_D] = invoke(mcad,'GetVariable','RMSPhaseCurrent_D');

% 14
% RMSPhaseCurrent_Q
[success,ResultMotorcadEmagPhasorDiagram.RMSPhaseCurrent_Q] = invoke(mcad,'GetVariable','RMSPhaseCurrent_Q');

% 15 Average Flux linkage when on load
% FluxLinkageLoad
[success,ResultMotorcadEmagPhasorDiagram.FluxLinkageLoad] = invoke(mcad,'GetVariable','FluxLinkageLoad');

% 16 Average Flux linkage along d axis when on load in [Vs] shown in phasor diagram[mVs]
% FluxLinkageLoad_D
[success,ResultMotorcadEmagPhasorDiagram.FluxLinkageLoad_D] = invoke(mcad,'GetVariable','FluxLinkageLoad_D');

% 17 Average Flux linkage along Q axis when on load
% FluxLinkageLoad_Q
[success,ResultMotorcadEmagPhasorDiagram.FluxLinkageLoad_Q] = invoke(mcad,'GetVariable','FluxLinkageLoad_Q');

% 18 Average Flux linkage along D axis when only Q axis current
% FluxLinkageQAxisCurrent_D
[success,ResultMotorcadEmagPhasorDiagram.FluxLinkageQAxisCurrent_D] = invoke(mcad,'GetVariable','FluxLinkageQAxisCurrent_D');

% 19 Inductance x Current (D axis)
% InductanceCurrent_D
[success,ResultMotorcadEmagPhasorDiagram.InductanceXCurrent_D] = invoke(mcad,'GetVariable','InductanceCurrent_D');
% 20 Inductance x Current (Q axis)
% InductanceCurrent_Q
[success,ResultMotorcadEmagPhasorDiagram.InductanceXCurrent_Q] = invoke(mcad,'GetVariable','InductanceCurrent_Q');


% 7 PhasorRmsPhaseVoltage
% no# PhasorRmsPhaseVoltage_D
% no# PhasorRmsPhaseVoltage_Q


end