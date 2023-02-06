
%% precondition
mcad_result_list_bydata=struct();
i=1;
%% define object
HDEV_motorcad=motorcaddata(12);
%% 

%% Infor regarding path
% HDEV_motorcad.proj_path='Z:\Thesis\HDEV\02_MotorCAD\MOT';
HDEV_motorcad.proj_path='Z:\01_Codes_Projects\Testdata_post\Simulation_Comparison';
HDEV_motorcad.file_name='12P72S_N42EH_Maxis_Br_95pro_LScoil_11T_2ndy_TestModel';
HDEV_motorcad.file_path=HDEV_motorcad.proj_path;
% file_list=fcn_read_dat(file_list_get(path),1)

%% basic drive &circuit data
HDEV_motorcad.Rs= 0.0067;   
HDEV_motorcad.Vdc=650;
HDEV_motorcad.Vs_max=HDEV_motorcad.Vdc*(2/pi)*0.98 % dankai
HDEV_motorcad.Is_max=750;     %pk value

%% data import
HDEV_motorcad=motorcad_fcn_result_export(HDEV_motorcad)
Jmag_Current=readtable(HDEV_motorcad.res);
Jmag_Current.Properties.VariableNames(1)={'time'}
% current
mcad_result_list_bydata.current.value=Jmag_Current; % measured fotmat 과 동일하게 맞추기 위해서 이걸 펑션으로 넣어야되는거아닌가

HDEV_motorcad.current=mcad_result_list_bydata.current;
HDEV_motorcad.current.value.Properties.Description='[A]'
HDEV_motorcad.current.time=mcad_result_list_bydata.current.value(:,1)

%temp
HDEV_motorcad.I1=HDEV_motorcad.current;
HDEV_motorcad.I1.value.Properties.VariableNames(2)={'data'}

HDEV_motorcad.I2=HDEV_motorcad.current;
HDEV_motorcad.I2.value.Properties.VariableNames(4)={'data'}

HDEV_motorcad.I3=HDEV_motorcad.current;
HDEV_motorcad.I3.value.Properties.VariableNames(3)={'data'}

% voltage
mcad_result_list_bydata.voltage.value=Jmag_Current;
HDEV_motorcad.u1(1).value.Properties.Description='[V]'


% rpm export
HDEV_motorcad.test_rpm=Jmag_fcn_get_setting_condition(HDEV_motorcad,'Motion','speed')
% HDEV_jmag.test_rpm(i)=
HDEV_motorcad.plot_rpm=HDEV_motorcad.test_rpm;

% time & degree -theta setting
t=HDEV_motorcad.current.time;
theta=HDEV_motorcad.wr_plot(i)*t.time;
init_angles=0;
deg_theta=rad2deg(theta)+init_angles;

%% dq trans

I_ins=[HDEV_motorcad.current.value.Coil1 HDEV_motorcad.current.value.Coil3 HDEV_motorcad.current.value.Coil2]';
% u_ins=[HDEV_jmag.u1.value.data HDEV_jmag.u3.value.data HDEV_jmag.u2.value.data]';


[xab,xdq]=dq_trans(I_ins,deg2rad(deg_theta)'); %% 입력이 3 x time 형태

I_ins=I_ins';
plot(t.time,I_ins)
hold on
plot(t.time,xdq')
hold on
mean_Idq=mean(xdq')
yline(mean_Idq)
hold on
text([mean(t.time(i))],[mean_Idq(1)],num2str(mean_Idq(1)))
hold on
text([mean(t.time(i))],[mean_Idq(2)],num2str(mean_Idq(2)))
formatter_sci

figure
plot(t.time,u_ins')
end

%% One elec period extract
HDEV_motorcad=fcn_One_period_sampling(HDEV_motorcad);
plot(HDEV_motorcad.Iabc.time, HDEV_motorcad.Iabc(:,1:3).Variables);

%% FFT - circuit
FFT_ia=fcn_fft_circuit(HDEV_motorcad,HDEV_motorcad.Iabc.Ia);
FFT_ib=fcn_fft_circuit(HDEV_motorcad,HDEV_motorcad.Iabc.Ib);
FFT_ic=fcn_fft_circuit(HDEV_motorcad,HDEV_motorcad.Iabc.Ic);

ia_N=length(FFT_ia);
ia_Side = FFT_ia(1:ia_N/2);
ia_angle_positive=rad2deg(angle(ia_Side));
ia_amp_positive= abs(ia_Side)/(ia_N/2);


ib_N=length(FFT_ib);
ib_Side = FFT_ib(1:ib_N/2);
ib_angle_positive=rad2deg(angle(ib_Side));
ib_amp_positive= abs(ib_Side)/(ib_N/2);

ic_N=length(FFT_ic);
ic_Side = FFT_ic(1:ic_N/2);
ic_angle_positive=rad2deg(angle(ic_Side));
ic_amp_positive= abs(ic_Side)/(ic_N/2);
% HDEV_measured.FFT_Iabc=table()
formatter_sci
breakyaxis([50 780]);


%% Flux linkage calculation


%% Inductance calculation

%% Phasor - fundamental & I-V-P-Q ->  Phi hi
for v=1:120
Ia(v).fft=[ia_amp_positive(1+v) ia_angle_positive(1+v)]
Ib(v).fft=[ib_amp_positive(1+v) ib_angle_positive(1+v)]
Ic(v).fft=[ic_amp_positive(1+v) ic_angle_positive(1+v)]
end

v=1
spplot(Ia(v).fft,Ib(v).fft,Ic(v).fft,Ia(5).fft,Ib(5).fft,Ic(5).fft)
hold on


spplot(Ia(v).fft,Ib(v).fft,Ic(v).fft)

%% 
% RmsBackEMFPhase
% RMSPhaseResistiveVoltage_D
% RMSPhaseResistiveVoltage_Q
% RMSPhaseResistiveVoltage
% RMSPhaseReactiveVoltage_D
% RMSPhaseReactiveVoltage_Q
% PhasorRmsPhaseVoltage
% RmsPhaseDriveVoltage
% PhaseVoltage
% PhasorLoadAngle
% PhasorPowerFactorAngle
% PhaseAdvance
% RMSPhaseCurrent

%% phasor diagram

%%
