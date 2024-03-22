function combineStruct=calcMcadPostPhasorDiagram(McadRaw,newRPM)
%% Frequency & Omega
if nargin>1
McadPost.freq_E=rpm2freqE(newRPM,McadRaw.Pole_Number/2);
McadPost.omegaE=freq2omega(McadPost.freq_E);
McadPost.RmsBackEMFPhase=McadRaw.RmsBackEMFPhase*newRPM/McadRaw.ShaftSpeed;
McadRaw.RmsBackEMFPhase=[];
McadRaw.ShaftSpeed=newRPM;
else
McadPost.freq_E=rpm2freqE(McadRaw.ShaftSpeed,McadRaw.Pole_Number/2);
McadPost.omegaE=freq2omega(McadPost.freq_E);
end
%% Resistance 
McadPost.ArmatureWindingResistancePh.value      =McadRaw.ArmatureWindingResistancePh   ;
McadPost.ArmatureWindingResistancePh.TempdegC   =McadRaw.ArmatureConductor_Temperature ;
McadPost.ArmatureEWdgMLTResistancePh.value      =McadRaw.ArmatureEWdgMLT_Calculated/McadRaw.ArmatureMLT*McadRaw.ArmatureWindingResistancePh;
McadPost.ArmatureWindingResistancePh.TempdegC   =McadRaw.ArmatureConductor_Temperature;
McadPost.ArmatureActiveMLTResistancePh.value    =(McadRaw.ArmatureMLT-McadRaw.ArmatureEWdgMLT_Calculated)/McadRaw.ArmatureMLT*McadRaw.ArmatureWindingResistancePh;
McadPost.ArmatureActiveMLTResistancePh.TempdegC =McadRaw.ArmatureConductor_Temperature;

%% dq current
[McadPost.PkPhaseCurrent_D,McadPost.PkPhaseCurrent_Q]=pkbeta2dq(rms2pk(McadRaw.RMSPhaseCurrent),McadRaw.PhaseAdvance);
McadPost.RMSPhaseCurrent_D=pk2rms(McadPost.PkPhaseCurrent_D);
McadPost.RMSPhaseCurrent_Q=pk2rms(McadPost.PkPhaseCurrent_Q);

% Q only Axis Current
[McadPost.pkQaxisOnlyCurrentD,McadPost.pkQaxisOnlyCurrentQ]=pkbeta2dq(rms2pk(McadRaw.RMSPhaseCurrent),180);
McadPost.RMSPhaseCurrent_DOnlyQ=pk2rms(McadPost.pkQaxisOnlyCurrentD);
McadPost.RMSPhaseCurrent_QOnlyQ=pk2rms(McadPost.pkQaxisOnlyCurrentQ);
%% Flux Linkage(Raw)

% FluxLinkageQAxisCurrent_D (Raw)
% Only Q Axis Current
McadRaw.FluxLinkageQAxisCurrent_D;  % D Flux link 
McadRaw.FluxLinkageQAxisCurrent_Q;  % Q Flux link 

%% Inductance (Raw & Calc)
McadRaw.InductanceLoad_D
McadRaw.InductanceLoad_Q

%% Voltage 
% Inductance X Current (calc & Raw Check) % InductanceCurrent (Calc) 
% This is 4 Reactive voltage
McadPost.InductanceDxCurrent_D=(McadRaw.InductanceLoad_D*McadPost.PkPhaseCurrent_D);
McadPost.InductanceQxCurrent_Q=(McadRaw.InductanceLoad_Q*McadPost.PkPhaseCurrent_Q);
        % difftol(input_obj.InductanceXCurrent_D,McadRaw.InductanceLoad_D*McadPost.PkPhaseCurrent_D,1e-3)
        % difftol(input_obj.InductanceXCurrent_Q,McadRaw.InductanceLoad_Q*McadPost.PkPhaseCurrent_Q,1e-3)
        % input_obj.InductanceXCurrent_D/(McadRaw.InductanceLoad_D*McadPost.PkPhaseCurrent_D)
        % input_obj.InductanceXCurrent_Q/(McadRaw.InductanceLoad_Q*McadPost.PkPhaseCurrent_Q)
%  Reactive Voltage (Phase RMS) = Inductance Voltage Drop
VRMSinductanceDropDaxis = -McadPost.omegaE*McadPost.InductanceQxCurrent_Q/sqrt(2);
VRMSinductanceDropQaxis =  McadPost.omegaE*McadPost.InductanceDxCurrent_D/sqrt(2);
McadPost.RMSPhaseReactiveVoltage_D=VRMSinductanceDropDaxis;
McadPost.RMSPhaseReactiveVoltage_Q=VRMSinductanceDropQaxis;
McadPost.absReativeVoltage=sqrt(VRMSinductanceDropDaxis.^2+VRMSinductanceDropDaxis.^2);

%  Resistivity Voltage (Phase RMS)
McadPost.RMSPhaseResistiveVoltage_D= McadPost.ArmatureWindingResistancePh.value*McadPost.RMSPhaseCurrent_D;
McadPost.RMSPhaseResistiveVoltage_Q= McadPost.ArmatureWindingResistancePh.value*McadPost.RMSPhaseCurrent_Q;
McadPost.RMSPhaseResistiveVoltage=sqrt(McadPost.RMSPhaseResistiveVoltage_D.^2+McadPost.RMSPhaseResistiveVoltage_Q.^2);

% Total Voltage
% McadPost.PhasorRMSPhaseVoltage=
%% dq Plane Out Bound

combineStruct=mergeStructs(McadRaw,McadPost);

end
