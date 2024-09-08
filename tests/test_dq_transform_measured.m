
HDEV_measured=measureddata(12)
% HDEV_measured.p=12;
%%
path='Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\Load\Test_20220313_2nd';
addpath(path)
measurelist_by_channel=fcn_read_dat(file_list_get(path),1)
%% data import
for i=1:1
% current
HDEV_measured.I1(1).value.Properties.Description='[A]'
HDEV_measured.I1=measurelist_by_channel.c1(1);
HDEV_measured.I2=measurelist_by_channel.c2(1);
HDEV_measured.I3=HDEV_measured.I2;
HDEV_measured.I3(1).value.data=-HDEV_measured.I1(1).value.data-HDEV_measured.I2(1).value.data;

%voltage
HDEV_measured.u1(1).value.Properties.Description='[V]'
HDEV_measured.u1=measurelist_by_channel.c3(1);
HDEV_measured.u2=measurelist_by_channel.c4(1);
HDEV_measured.u3=HDEV_measured.u2;
HDEV_measured.u3.value.data=-HDEV_measured.u1(1).value.data-HDEV_measured.u2(1).value.data;

%current
HDEV_measured.I1(i,1)=measurelist_by_channel.c1(i);
HDEV_measured.I2(i,1)=measurelist_by_channel.c2(i);
HDEV_measured.I3=HDEV_measured.I2;
HDEV_measured.I3(i,1).value.data=-HDEV_measured.I1(i).value.data-HDEV_measured.I2(i).value.data;

% time & degree -theta setting
HDEV_measured.test_rpm(i)=str2num(measurelist_by_channel.c1(i).rpm)
% HDEV_measured.wr_test(i)= 2*pi*HDEV_measured.test_rpm(i)/60*HDEV_measured.p/2
% HDEV_measured.wr_plot(i)= 2*pi*HDEV_measured.test_rpm(i)/60*HDEV_measured.p/2

t=HDEV_measured.I1(i).time;
theta=HDEV_measured.wr_plot(i)*t.time;
init_angles=90;
deg_theta=rad2deg(theta+init_angles);

%% dq trans
I_ins=[HDEV_measured.I1(i).value.data HDEV_measured.I3(i).value.data HDEV_measured.I2(i).value.data]';
u_ins=[HDEV_measured.u1.value.data HDEV_measured.u3.value.data HDEV_measured.u2.value.data]';


[xab,xdq]=dq_trans(I_ins,deg2rad(deg_theta)'); %% 입력이 3 x time 형태
HDEV_measured.Id=xdq(1,:)';
HDEV_measured.Iq=xdq(2,:)';

I_ins=I_ins';
figure(1)
plot(t.time,I_ins)
hold on
plot(t.time,xdq')

mean_Idq=mean(xdq')
yline(mean_Idq)
hold on
text([mean(t.time(i))],[mean_Idq(1)],num2str(mean_Idq(1)))
hold on
text([mean(t.time(i))],[mean_Idq(2)],num2str(mean_Idq(2)))
formatter_sci

figure(2)
plot(t.time,u_ins')
end

%% One elec period extract
HDEV_measured=fcn_One_period_sampling(HDEV_measured);
plot(HDEV_measured.Iabc.time, HDEV_measured.Iabc(:,1:3).Variables);

%% FFT - circuit
FFT_ia=fcn_fft_circuit(HDEV_measured,HDEV_measured.Iabc.Ia,1);
FFT_ib=fcn_fft_circuit(HDEV_measured,HDEV_measured.Iabc.Ib,1);
FFT_ic=fcn_fft_circuit(HDEV_measured,HDEV_measured.Iabc.Ic,1);

%dq fft
HDEV_measured.FFT_Idq.Id=fcn_fft_circuit(HDEV_measured,HDEV_measured.Id,0);
HDEV_measured.FFT_Idq.Iq=fcn_fft_circuit(HDEV_measured,HDEV_measured.Iq,0);
% figure
% HDEV_measured.dq_phasor_diagram

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
breakyaxis([50 78]);


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
