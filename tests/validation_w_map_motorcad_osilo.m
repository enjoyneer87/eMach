%% 
% Reduced  node model 만들기
%% 
% 
%% 1  전류입력 위상각 찾기
% 온도상승시험시(OP1 20210909)
%% 
% * 맵데이터 찾기
%% 
% Import map(국민대 제어) 

cd Z:\01_Codes_Projects\Testdata_post
Map_plot_Ipk_beta_Torque
[data row_array]=max(torque_map);
[data col]=max(max(torque_map));
row =row_array(col);

Ipk_Tmax_testmap=Ipk(row, col);
beta_Tmax_testmap=beta(row,col);

% 멥데이터와 온도상승시험시 오실로 데이터 측정값 비교
% (한자연 lecroy 오실로 4채널 )

% 20210909   3채널 전류  
cd Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\Load\Test_20210909\20210909
file_path=cd
Import_waveform


% 20220323 2채널 전류 2채널 전압
cd Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\Load\Test_2nd\temperature_rise_test
file_path=cd
VI_osilo_temp_rise_test
% Ipk_Tmax_osilo=
% beta_Tmax=

%% 2. 넣어서 motorcad emag 돌리기

mcad = actxserver('MotorCAD.AppAutomation');
invoke(mcad,'SetVariable','PeakCurrent',Ipk_Tmax_testmap);
% invoke(mcad,'SetVariable','PeakCurrent',Ipk_Tmax_testmap);

% invoke(mcad,'SetVariable','PhaseAdvance',beta_Tmax_testmap);


success = invoke(mcad,'DoMagneticCalculation');
if success == 0
    disp('Magnetic calculation successfully completed');
else
    disp('Magnetic calculation failed');
end
% Jmag analysis data import

formatSpec='%.2f';


cd D:\KDH\Thesis\HDEV\01_JMAG\Jproject
phase_current= readtable("D:\KDH\Thesis\HDEV\01_JMAG\Jproject\phase_current.csv");
% phase_current(1:2,:) = [];
torque_em= readtable("D:\KDH\Thesis\HDEV\01_JMAG\Jproject\torque_em.csv");
phase_v= readtable("D:\KDH\Thesis\HDEV\01_JMAG\Jproject\phase_v.csv");


Power_Input=phase_current.Coil1_Case1_.*phase_v.Terminal1_Case1_+phase_current.Coil2_Case1_.*phase_v.Terminal2_Case1_+phase_current.Coil3_Case1_.*phase_v.Terminal3_Case1_
Power_Input=Power_Input(2:121);
ShaftSpeed=1000
omega= ShaftSpeed/60*2*pi;
Electromagnetic_Power=torque_em.Torque_Case1_(2:121)*omega;

subplot(3,2,1:4)
plot(0:360/120:360-3,[Electromagnetic_Power Power_Input]);
legend('Power_T_{em}','Power_{Input}');
yline([mean(Electromagnetic_Power) mean(Power_Input)])
xlabel('Rotor angle(EDeg)')
ylabel('Power[W]')

meanpower_em=num2str(mean(Electromagnetic_Power)/1000,formatSpec);
meanpower_input=num2str(mean(Power_Input)/1000,formatSpec);
meanpower_em=strcat("Power",meanpower_em,'[kW]');
meanpower_input=strcat("Power",meanpower_input,'[kW]');
text(120,mean(Electromagnetic_Power),meanpower_em);
text(120,mean(Power_Input),meanpower_input);

subplot(3,2,5)
plot(0:360/120:360-3, [ phase_current.Coil1_Case1_(2:121) phase_current.Coil2_Case1_(2:121) phase_current.Coil3_Case1_(2:121)]);
xlabel('Rotor Position (EDeg)');
ylabel('Phase Current [A]');
 
subplot(3,2,6)
plot(0:360/120:360-3, [phase_v.Terminal1_Case1_(2:121) phase_v.Terminal2_Case1_(2:121) phase_v.Terminal3_Case1_(2:121)]);
xlabel('Rotor Position (EDeg)');
ylabel('Terminal Voltage[V]');


% motorcad analysis data plot

[success,PointsPerCycle] = invoke(mcad,'GetVariable','TorquePointsPerCycle');
[success,NumberCycles] = invoke(mcad,'GetVariable','TorqueNumberCycles');

NumTorquePoints = (PointsPerCycle * NumberCycles) + 1;
RotorPosition = zeros(NumTorquePoints, 1);
TerminalVoltage1 = zeros(NumTorquePoints, 1);
PhaseCurrent1 = zeros(NumTorquePoints, 1);
TerminalVoltage2 = zeros(NumTorquePoints, 1);
PhaseCurrent2 = zeros(NumTorquePoints, 1);
TerminalVoltage3 = zeros(NumTorquePoints, 1);
PhaseCurrent3 = zeros(NumTorquePoints, 1);

for loop = 0:NumTorquePoints-1
    [success,x,uV] = invoke(mcad,'GetMagneticGraphPoint','TerminalVoltage1', loop);
    [success,x,uI] = invoke(mcad,'GetMagneticGraphPoint','PhaseCurrent1', loop);
    [success,x,vV] = invoke(mcad,'GetMagneticGraphPoint','TerminalVoltage2', loop);
    [success,x,vI] = invoke(mcad,'GetMagneticGraphPoint','PhaseCurrent2', loop);
    [success,x,wV] = invoke(mcad,'GetMagneticGraphPoint','TerminalVoltage3', loop);
    [success,x,wI] = invoke(mcad,'GetMagneticGraphPoint','PhaseCurrent3', loop);
    [success,x,y] = invoke(mcad,'GetMagneticGraphPoint','TorqueVW', loop);

  
    if success == 0
        RotorPosition(loop+1) = x;
        TerminalVoltage1(loop+1) = uV;
        PhaseCurrent1(loop+1) = uI;
        TerminalVoltage2(loop+1) = vV;
        PhaseCurrent2(loop+1) = vI;
        TerminalVoltage3(loop+1) = wV;
        PhaseCurrent3(loop+1) = wI;
        TorqueVW(loop+1) = y;
    end
end


[success,ElectromagneticPower] = invoke(mcad,'GetVariable','ElectromagneticPower');
[success,InputPower] = invoke(mcad,'GetVariable','InputPower');

Electromagnetic_Power=TorqueVW*omega;
figure(1);

plot(RotorPosition, TorqueVW);
title('Torque');
xlabel('Rotor Position (EDeg)');
ylabel('Torque (VW)');

% Instaneouse power calculation with phase voltage(3rd harmonic c
Inst_power_motorcad=power_calculation_3p3w(TerminalVoltage1,TerminalVoltage2,TerminalVoltage3,PhaseCurrent1,PhaseCurrent2,PhaseCurrent3)

subplot(3,2,1:4)
plot(RotorPosition, [Inst_power_motorcad.p_total Electromagnetic_Power' ] )
xlabel('Rotor Position (EDeg)');
ylabel('Power[W]');
 

subplot(3,2,5)
plot(RotorPosition, [ PhaseCurrent1 PhaseCurrent2 PhaseCurrent3]);
xlabel('Rotor Position (EDeg)');
ylabel('Phase Current [A]');
 
subplot(3,2,6)
plot(RotorPosition, [TerminalVoltage3 TerminalVoltage2 TerminalVoltage1]);
xlabel('Rotor Position (EDeg)');
ylabel('Terminal Voltage[V]');


% Data import for phasor diagram

% 1
% RmsBackEMFPhase
[success,RmsBackEMFPhase] = invoke(mcad,'GetVariable','RmsBackEMFPhase');


% 2 The rms D axis Phase resistive Voltage
% RMSPhaseResistiveVoltage_D
[success,RMSPhaseResistiveVoltage_D] = invoke(mcad,'GetVariable','RMSPhaseResistiveVoltage_D');

% 3 The rms Q axis Phase resistive Voltage
% RMSPhaseResistiveVoltage_Q
[success,RMSPhaseResistiveVoltage_Q] = invoke(mcad,'GetVariable','RMSPhaseResistiveVoltage_Q');

% 4 The rms Phase resistive Voltage
% RMSPhaseResistiveVoltage
[success,RMSPhaseResistiveVoltage] = invoke(mcad,'GetVariable','RMSPhaseResistiveVoltage');

% 5 The reactive voltage drop D axis (Q axis current x Q axis inductance)
% RMSPhaseReactiveVoltage_D
[success,RMSPhaseReactiveVoltage_D] = invoke(mcad,'GetVariable','RMSPhaseReactiveVoltage_D');
% 6 The reactive voltage drop in Q axis (D axis current x D axis inductance)
% RMSPhaseReactiveVoltage_Q
[success,RMSPhaseReactiveVoltage_Q] = invoke(mcad,'GetVariable','RMSPhaseReactiveVoltage_Q');

% 7 The rms Phase Voltage at the terminals of the machine from phasor diagram
% PhasorRmsPhaseVoltage
[success,PhasorRmsPhaseVoltage] = invoke(mcad,'GetVariable','PhasorRmsPhaseVoltage');
% The required rms Phase Voltage at the output of the drive taking into account sine filter
% RmsPhaseDriveVoltage
[success,RmsPhaseDriveVoltage] = invoke(mcad,'GetVariable','RmsPhaseDriveVoltage');

% 8 The rms Phase Voltage at the output of the supply
% PhaseVoltage
[success,PhaseVoltage] = invoke(mcad,'GetVariable','PhaseVoltage');

% 9  Load Angle from phasor diagram
% PhasorLoadAngle 
[success,PhasorLoadAngle] = invoke(mcad,'GetVariable','PhasorLoadAngle');

% 10 Power Factor Angle from phasor diagram
% PhasorPowerFactorAngle
[success,PhasorPowerFactorAngle] = invoke(mcad,'GetVariable','PhasorPowerFactorAngle');

% 11 The phase advance in electrical degrees
% PhaseAdvance
[success,PhaseAdvance] = invoke(mcad,'GetVariable','PhaseAdvance');

% 12 The calculated rms phase current
% RMSPhaseCurrent
[success,RMSPhaseCurrent] = invoke(mcad,'GetVariable','RMSPhaseCurrent');

% 13 
% RMSPhaseCurrent_D
[success,RMSPhaseCurrent_D] = invoke(mcad,'GetVariable','RMSPhaseCurrent_D');

% 14
% RMSPhaseCurrent_Q
[success,RMSPhaseCurrent_Q] = invoke(mcad,'GetVariable','RMSPhaseCurrent_Q');

% 15 Average Flux linkage when on load
% FluxLinkageLoad
[success,FluxLinkageLoad] = invoke(mcad,'GetVariable','FluxLinkageLoad');

% 16 Average Flux linkage along d axis when on load in [Vs] shown in phasor diagram[mVs]
% FluxLinkageLoad_D
[success,FluxLinkageLoad_D] = invoke(mcad,'GetVariable','FluxLinkageLoad_D');

% 17 Average Flux linkage along Q axis when on load
% FluxLinkageLoad_Q
[success,FluxLinkageLoad_Q] = invoke(mcad,'GetVariable','FluxLinkageLoad_Q');

% 18 Average Flux linkage along D axis when only Q axis current
% FluxLinkageQAxisCurrent_D
[success,FluxLinkageQAxisCurrent_D] = invoke(mcad,'GetVariable','FluxLinkageQAxisCurrent_D');

% 19 Inductance x Current (D axis)
% InductanceCurrent_D
[success,InductanceCurrent_D] = invoke(mcad,'GetVariable','InductanceCurrent_D');
% 20 Inductance x Current (Q axis)
% InductanceCurrent_Q
[success,InductanceCurrent_Q] = invoke(mcad,'GetVariable','InductanceCurrent_Q');

% PhasorPowerFactor
% PhasorLoadAngle
% PhasorRmsPhaseVoltage
% PhasorRmsPhaseVoltage_D
% PhasorRmsPhaseVoltage_Q
% phasor plot

% current plot

quiver(0,0,RMSPhaseCurrent_D,0,'off','b');
hold on 
quiver(RMSPhaseCurrent_D,0,0,RMSPhaseCurrent_Q,'off','b');
hold on
quiver(0,0,RMSPhaseCurrent_D,RMSPhaseCurrent_Q,'off','b')

hold on
% Flux Linkage
quiver(0,0,1000*FluxLinkageLoad_D,0,'off','g');
hold on
quiver(1000*FluxLinkageLoad_D,0,0,1000*FluxLinkageLoad_Q,'off','g');
hold on
quiver(0,0,1000*FluxLinkageLoad_D,1000*FluxLinkageLoad_Q,'off','g');
hold on

quiver(0,0,1000*FluxLinkageQAxisCurrent_D,0,'off','g');
hold on
quiver(1000*FluxLinkageQAxisCurrent_D,0,0,1000*InductanceCurrent_Q,'off','g');
hold on
quiver(1000*FluxLinkageQAxisCurrent_D,1000*InductanceCurrent_Q,1000*InductanceCurrent_D,0,'off','g');

% Voltage plot
quiver(0,0,0,RmsBackEMFPhase,'off','r');
hold on
quiver(0,RmsBackEMFPhase,RMSPhaseResistiveVoltage_D,RMSPhaseResistiveVoltage_Q,'off','r');
hold on
quiver(RMSPhaseResistiveVoltage_D,RmsBackEMFPhase+RMSPhaseResistiveVoltage_Q,0,RMSPhaseReactiveVoltage_Q,'off','r');
hold on
quiver(RMSPhaseResistiveVoltage_D,RmsBackEMFPhase+RMSPhaseResistiveVoltage_Q+RMSPhaseReactiveVoltage_Q,RMSPhaseReactiveVoltage_D,0,'off','r');
hold on
quiver(0,0,RMSPhaseResistiveVoltage_D+RMSPhaseReactiveVoltage_D,RmsBackEMFPhase+RMSPhaseResistiveVoltage_Q+RMSPhaseReactiveVoltage_Q,'off','r');

centers = [0 0];
radii = RMSPhaseCurrent
% radii =150
viscircles(centers,radii)
% 
% feather(RMSPhaseCurrent_D,RMSPhaseCurrent_Q);
% plot(RMSPhaseCurrent_Q)
% Power Calculation

% Average torque (FE)  The average airgap torque from virtual work and Maxwell stress finite element methods
 

% ElectromagneticPower
% Electromagnetic power of machine = Average torque (FE) x shaft speed [rad/s]. 
% If the operating point is outside of or near to the voltage limit this variable is highlighted in red or purple.
[success,ElectromagneticPower] = invoke(mcad,'GetVariable','ElectromagneticPower');

% input power = output power + total machine losses on load
[success,InputPower] = invoke(mcad,'GetVariable','InputPower');

% OutputPower : power at the shaft = electromagnetic power - (core + mechanical losses).
% Mechanical output power (electromagnetic power less losses)
% If the operating point is outside of or near to the voltage limit this variable is highlighted in red or purple.
[success,OutputPower] = invoke(mcad,'GetVariable','OutputPower');
% Electrical output power (mechanical power less losses)
[success,OutputPower_Mechanical] = invoke(mcad,'GetVariable','OutputPower_Mechanical');
[success,OutputPower_Electrical] = invoke(mcad,'GetVariable','OutputPower_Electrical');
% TotalLoss :Total machine losses on load = (core, magnet, retaining sleeve losses) + mechanical losses + DC conductor losses + AC conductor losses
[success,TotalLoss] = invoke(mcad,'GetVariable','TotalLoss');

% Torque at shaft of machine taking into account drag losses
% Shaft Torque - Average Torque (FE) - (core + mechanical loss)/speed[rad/s]
[success,ShaftTorque] = invoke(mcad,'GetVariable','ShaftTorque');
% Torque calculation
[success,AvTorqueVW] = invoke(mcad,'GetVariable','AvTorqueVW');
[success,AvTorqueMS] = invoke(mcad,'GetVariable','AvTorqueMS');
[success,AvTorqueMS] = invoke(mcad,'GetVariable','AvTorqueMS');
[success,AvTorqueMsVw] = invoke(mcad,'GetVariable','AvTorqueMsVw');
[success,AvTorqueDQ] = invoke(mcad,'GetVariable','AvTorqueDQ');
[success,AvTorqueEC] = invoke(mcad,'GetVariable','AvTorqueEC');
% DC Loss
[success,ConductorLoss] = invoke(mcad,'GetVariable','ConductorLoss');
% AC Loss
[success,FEAProxLosses_OnLoad_Total] = invoke(mcad,'GetVariable','FEAProxLosses_OnLoad_Total');

%  Magnet Loss
[success,MagnetLoss] = invoke(mcad,'GetVariable','MagnetLoss');


%  core loss
[success,StatorIronLoss_Total] = invoke(mcad,'GetVariable','StatorIronLoss_Total');
[success,RotorIronLoss_Total] = invoke(mcad,'GetVariable','RotorIronLoss_Total');
[success,StatorIronLossBuildFactor] = invoke(mcad,'GetVariable','StatorIronLossBuildFactor');
[success,RotorIronLossBuildFactor] = invoke(mcad,'GetVariable','RotorIronLossBuildFactor');

IronLoss=StatorIronLoss_Total*StatorIronLossBuildFactor+RotorIronLoss_Total*RotorIronLossBuildFactor;
%  mechanical loss
[success,Friction_Loss_F_ref] = invoke(mcad,'GetVariable','Friction_Loss_[F]_@Ref_Speed');
[success,Friction_Loss_R_ref] = invoke(mcad,'GetVariable','Friction_Loss_[R]_@Ref_Speed');
[success,Ref_Speed_Friction_Loss_F] = invoke(mcad,'GetVariable','Ref_Speed_-_Friction_Loss_[F]');
[success,Ref_Speed_Friction_Loss_R] = invoke(mcad,'GetVariable','Ref_Speed_-_Friction_Loss_[R]');

[success,Friction_F] = invoke(mcad,'GetVariable','Loss_[Friction_-_F_Bearing]');
[success,Friction_R] = invoke(mcad,'GetVariable','Loss_[Friction_-_R_Bearing]');

[success,ShaftSpeed] = invoke(mcad,'GetVariable','ShaftSpeed');



omega= ShaftSpeed/60*2*pi;
% freq_mech=2100/60;
% omega=freq_mech*2*pi

% Friction Loss model
Friction_Loss_F=ShaftSpeed/Ref_Speed_Friction_Loss_F*Friction_Loss_F_ref;
Friction_Loss_R=ShaftSpeed/Ref_Speed_Friction_Loss_R*Friction_Loss_R_ref;
Friction_Loss =Friction_Loss_F_ref+Friction_Loss_R_ref

% Friction Loss Input
Friction_Loss=Friction_F+Friction_R;

% Magnet Loss Model
[success,MagnetLoss] = invoke(mcad,'GetVariable','MagnetLoss');

[success,Magnet2D3DFactor] = invoke(mcad,'GetVariable','Magnet2D3DFactor');
[success,MagnetLossBuildFactor] = invoke(mcad,'GetVariable','MagnetLossBuildFactor');

MagnetLoss=MagnetLoss*MagnetLossBuildFactor

% Check
% Porwer_summary=[(ElectromagneticPower-Friction_Loss-IronLoss) OutputPower InputPower ElectromagneticPower Friction_Loss IronLoss]
% Full AC loss FEA
Power_summary=[(ElectromagneticPower-Friction_Loss-IronLoss-MagnetLoss) OutputPower InputPower ElectromagneticPower Friction_Loss IronLoss]

Torque_summary=[InputPower/omega OutputPower/omega ElectromagneticPower/omega Friction_Loss/omega IronLoss/omega]
%shaft_torque_check=[ShaftTorque (ElectromagneticPower-Friction_Loss-IronLoss)/omega ElectromagneticPower/omega]
shaft_torque_check=[ShaftTorque (ElectromagneticPower-Friction_Loss-IronLoss-MagnetLoss)/omega ElectromagneticPower/omega]

torque_check=[ElectromagneticPower/omega AvTorqueMsVw]
Effyciency=OutputPower/InputPower*100


%% This is a study for a proposal of a machine design paper format concerning the special session of ECCE 2021
% Reproducibility, Tracebiltiy, Auditability
% 
% Inevitably, In case of design paper, the desicion making process and criteria 
% should be logically argued and qunatatilbly clarified in terms of fullfillment 
% of requirement(specification).
%% 
% * Clarify the Input for specific output
%% 
% 
%% 
% * preferable UQ
%% 
% 
%% 
% * Lack of explanation regarding Gap between simulation and experimental Voltage 
% utilization especially in FW region.
% * Instaneous Power balance problem of Backward euler method using Finite element 
% midethod
% * Fail of Instaneous Power balance in system simulation that cont`ains electric 
% machine model.


%% 3.  [To do] Check motor result & compare with      efficiency test result (Torque & Efficiency (Input (V, I) vs Output(shaft torque & loss)
% 
% 
% 
% 
% 
% 
% 
%% 4. Plot temperature rise curve 
% (20210909~10)
% 
% 
% 

cd Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\Load\Test_20210909\20210909\Temp_rise
f=1
op1_temp=temp_data_import("20210909-op1_30lpm-back_up_11.csv")
Temp_rise_plot
[cool_down_data legend_name_experiment]=fcn_cool_down_plot(op1_temp)
restart_cool_down_data=retime_start_from_zero(cool_down_data,time_step)

f=2
op1_temp=temp_data_import("20210909-op1_30lpm-back_up_07.csv")
Temp_rise_plot

f=3
op1_temp=temp_data_import("20210909-op1_30lpm-back_up_10.csv")
Temp_rise_plot
f=4
op1_temp=temp_data_import("20210910-op2_30lpm-back_up_01.csv")
Temp_rise_plot
cool_down_plot
% (20220323)

cd Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\Load\Test_2nd\temperature_rise_test\temperature
load('Op2_temp_20220323.mat')
Daily20220323112136op2rename=readtable("Daily20220323112136_op2_rename.csv")
% table data 정리
op2_temp_rise=Daily20220323112136op2rename(1:end-1,:); 

names=op2_temp_rise.Properties.VariableNames
tf= contains(op2_temp_rise.Properties.VariableNames,'CH') 
names=names(tf)
op2_temp_rise=op2_temp_rise(:,[names])

tf= contains(op2_temp_rise.Properties.VariableNames,'Time')==0
names=names(tf)
op2_temp_rise=op2_temp_rise(:,[names])


clearvars Daily20220323112136op2rename
sample_second=1 %sec
sample_second=seconds(1)

op2_temp_rise = table2timetable(op2_temp_rise,'TimeStep',sample_second,'StartTime',seconds(0))
width(op2_temp_rise)
for i=6:width(op2_temp_rise)
if all(op2_temp_rise.(op2_temp_rise.Properties.VariableNames{i})>=20) && all(contains(op2_temp_rise.Properties.VariableNames{i},'Average')==1) && all(contains(op2_temp_rise.Properties.VariableNames{i},'coil')==1)  %|| all(contains(op2_temp_rise.Properties.VariableNames{i},'coil')==1) 
    figure(1)
    scatter(op2_temp_rise.Time,op2_temp_rise.(op2_temp_rise.Properties.VariableNames{i}),'DisplayName',op2_temp_rise.Properties.VariableNames{i})
  ylabel("Temperature")
    xlabel("seconds")
    legend
    hold on
end

end
%% 
% 
% 
% 

% Time_data=op2_temp_rise.Variables;
% init_time=Time_data(1)
% last_time=Time_data(end)
% last_time=Time_data(end-1)
% time_range=last_time-init_time
% [Y M D H M S]=datevec(time_range);
% time_range=M*60+S
%% 
% 4.  [To do ]]Adjust loss with Test Value  -> Input loss
% 
% 


%% 5. Reduced Node Model (RNM) 

% by hands 

%% steady-state Full model vs RNM validation

% copy to validation (RNM)
% save node selection(Locked node)

%% Transient Full mode vs RNM validation
% Transient Graph interface -> (load Locked node) Full model vs RNM comparison




%  Heat Transfer Correlation

% 
% invoke(mcad,'SetVariable','Calc/Input_h[WJ]_Rear_Housing',1);
% 
% invoke(mcad,'SetArrayVariable','HousingWJ_CalcInputH_A',0,1);
% 
% [success,WJ_Fluid_K] = invoke(mcad,'GetVariable','WJ_Fluid_Thermal_Conductivity');
% [success,WJ_Fluid_Rho] = invoke(mcad,'GetVariable','WJ_Fluid_Density');
% [success,WJ_Fluid_Mu] = invoke(mcad,'GetVariable','WJ_Fluid_Dynamic_Viscosity');
% [success,WJ_Fluid_U_A] = invoke(mcad,'GetArrayVariable','HousingWJ_Velocity_A',0);
% [success,WJ_Fluid_U_R] = invoke(mcad,'GetVariable','WJ_Channel_Fluid_Velocity_[Rear]');
% 
% h_A = 0.005 * WJ_Fluid_K * WJ_Fluid_Rho * WJ_Fluid_U_A / WJ_Fluid_Mu;
% h_R = 0.005 * WJ_Fluid_K * WJ_Fluid_Rho * WJ_Fluid_U_R / WJ_Fluid_Mu;
% 
% invoke(mcad,'SetArrayVariable','HousingWJ_InputH_A', 0, h_A);
% invoke(mcad,'SetVariable','Input_Value_h[WJ]_Rear_Housing', h_R);


%% 6. Calibration (by parameter estimation app in Simplified simulink model)
% [To do] Stiffness Matrix를 input으로 매칭해서 error최소화 
% Define Input parameter (최적화 변수 )

%I/O w Motor-CAD
mcad = actxserver('MotorCAD.AppAutomation');

x_in_MotorCAD=struct();
K_Axial_User_A=10;
K_Radial_User_A=10;
mcad.SetVariable('K_Axial_User_A',K_Axial_User_A)
% mcad.SetVariable('K_Axial_User_R',K_Axial_User_R)
% mcad.SetVariable('K_Axial_User_F',K_Axial_User_F)
[success,K_Axial_User_A]=mcad.GetVariable('K_Axial_User_A')   


% clear
mcad = actxserver('MotorCAD.AppAutomation');

% x_in_MotorCAD=struct();
% x=2000;



% K_Axial_User_A=x;
mcad.SetVariable('K_Axial_User_A',K_Axial_User_A)
mcad.SetVariable('K_Radial_User_A',K_Radial_User_A)

% mcad.SetVariable('K_Axial_User_R',K_Axial_User_R)
% mcad.SetVariable('K_Axial_User_F',K_Axial_User_F)
% [success,K_Axial_User_A]=mcad.GetVariable('K_Axial_User_A')   

% calculate steady-state
mcad.DoSteadyStateAnalysis
% export matrix
matrixpath='Z:\01_Codes_Projects\Testdata_post\Simulation_Comparison\12P72S_N42EH_Br_95pro_11T_Fidelity_study_calibrate_2D\MatrixExportData\RNM2\'
cd(matrixpath)
% delete(strcat(matrixpath,'*'));

% mcad.SetVariable('MatrixTextSeparator',';')
% mcad.ExportMatrices(matrixpath)

%% 
% export the validated RNM matrices or Full model matrices

% % Export RNM matrices from Motor-CAD
% matrixpath='Z:\01_Codes_Projects\Testdata_post\Simulation_Comparison\12P72S_N42EH_Br_95pro_11T_Fidelity_study_calibrate_2D\MatrixExportData\RNM2\'
% mcad.SetVariable('MatrixTextSeparator',';')
% mcad.ExportMatrices(matrixpath)

Thermal_matrix_file_name='12P72S_N42EH_Br_95pro_11T_Fidelity_study_calibrate_2D'
Loss_Factor = [0, 0, 0, 0];

% Import to Simulink
slx_file_path='Z:\01_Codes_Projects\Testdata_post\Simulation_Comparison\12P72S_N42EH_Br_95pro_11T_Fidelity_study_calibrate_2D\MatrixExportData'
cd(slx_file_path)
Simplified_Thermal_CircuitIN_Matlab_kdh_Validation
sim('Simplified_Thermal_Circuit.slx');
%% 
% Reference Measured Data 

% one of this data op1_temp
fcn_cool_down_plot(op1_temp)

%% 
% Simulation Output Should be Output of Simulink

output_sqeeze=squeeze(out.ScopeData1{1}.Values.Data(:,1,:));
f=figure
movegui(f,'center');
plot(output_sqeeze(220,:));
%% 
% 에러 정의 (목적함수)

Error = evalRequirement_kdh(r,Sig.Values,EstimationData.OutputData.Values);

% signalTracking_error_definition_kdh(x,)
% sdo.requirements.SignalTracking
F_r = [F_r; Error(:)];

%% 
% 


%% 
% Optimization Probelm 정의 

% Plot Measured Temperature
t=seconds(cool_down_data.Time)

% t = Data(:,1);
y = cool_down_data.V
f = figure;
movegui(f,'center');
plot(t,y,'ro')
% 
fun = @(x)x(1)*exp(-t).*exp(-exp(-(t-x(2)))) - y;



x0 = [1/2,0];
x = lsqnonlin(fun,x0)

hold on


plot(t,fun(x)+y,'b-')
% hold off
%% 
% [parameter estimator예시  ]SSC_motor_thermal 

% Excute parameter estimator
% [tout,yout]

op1_temp=table2timetable(op1_temp,'TimeStep',time_step,"StartTime",seconds(0));



Exp = sdo.Experiment('Simplified_Thermal_Circuit');

[Temperature_Output a b ] =sim('ssc_motor_thermal_circuit_sensitivity');

%% Optimization Options
%
% Specify optimization options.
Options = sdo.OptimizeOptions;
Options.Method = 'lsqnonlin';
Options.OptimizedModel = Simulator;

optimfcn = @(P) ssc_motor_thermal_circuit_sensitivity_optFcn(P,Simulator,Exp);

[pOpt,Info] = sdo.optimize(optimfcn,p,Options);