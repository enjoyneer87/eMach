%% precondition
global jmag_version
jmag_version='210'
result_list_bydata=struct();
i=1;
% define object
HDEV_jmag=JmagData(12);
% Infor regarding path
HDEV_jmag.jproj_path='D:\KDH\Thesis\HDEV\01_JMAG\Jproject';
HDEV_jmag.file_name='12p72_HDEV_1st_year_RT_20201019'
HDEV_jmag.file_path=strcat(HDEV_jmag.jproj_path,'\',HDEV_jmag.file_name);
HDEV_jmag.jmag_version=jmag_version;
% path='Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\Load\Test_20220313_2nd';
% file_list=fcn_read_dat(file_list_get(path),1)
%% Input 정의 
% basic drive &circuit data
HDEV_jmag.Rs= 0.0067;   
HDEV_jmag.Vdc=650;
HDEV_jmag.Vs_max=HDEV_jmag.Vdc*(2/pi)*0.98 % dankai
HDEV_jmag.Is_max=750;     %pk value
%% Output 정의 -  List the data wanted to export or plot 
% cell format - python list와의 유사성 때문
o_data_name=acceptVariableNumInputs('LineCurrent','Torque');
% o_data_name=cell(1,2);
% 
% o_data_name{1,1}={'LineCurrent'};
% o_data_name{1,2}={'LineCurrent'};
% celldisp(o_data_name);
% other format - struct or table 

%% data format to Simul object - 상호간의 구조 allocation이 필요할듯
HDEV_jmag.outputName=o_data_name;
length(o_data_name);

%% data import
out=HDEV_jmag.jmagFcnResultExport;

Jmag_Current=readtable(HDEV_jmag.res{1});
% t1=readtable('Torque1.csv')
Jmag_Current.Properties.VariableNames(1)={'time'};
% current
result_list_bydata.current.value=Jmag_Current; % measured fotmat 과 동일하게 맞추기 위해서 이걸 펑션으로 넣어야되는거아닌가

HDEV_jmag.current=result_list_bydata.current;
HDEV_jmag.current.value.Properties.Description='[A]'
HDEV_jmag.current.time=result_list_bydata.current.value(:,1)


%temp
HDEV_jmag.I1=HDEV_jmag.current;
HDEV_jmag.I1.value.Properties.VariableNames(2)={'data'}

HDEV_jmag.I2=HDEV_jmag.current;
HDEV_jmag.I2.value.Properties.VariableNames(4)={'data'}

HDEV_jmag.I3=HDEV_jmag.current;
HDEV_jmag.I3.value.Properties.VariableNames(3)={'data'}

% voltage
result_list_bydata.voltage.value=Jmag_Current;
HDEV_jmag.u1(1).value.Properties.Description='[V]'


% rpm export
HDEV_jmag.test_rpm=Jmag_fcn_get_setting_condition(HDEV_jmag,'Motion','speed')
% HDEV_jmag.test_rpm(i)=


% time & degree -theta setting
t=HDEV_jmag.current.time;
theta=HDEV_jmag.wr_plot(i)*t.time;
init_angles=0;
deg_theta=rad2deg(theta)+init_angles;

%% dq trans

I_ins=[HDEV_jmag.current.value.Coil1 HDEV_jmag.current.value.Coil3 HDEV_jmag.current.value.Coil2]';
% u_ins=[HDEV_jmag.u1.value.data HDEV_jmag.u3.value.data HDEV_jmag.u2.value.data]';
%%%%%
input_obj=HDEV_jmag

[xab,xdq]=dq_trans(I_ins,deg2rad(deg_theta)'); %% 입력이 3 x time 형태

I_ins=I_ins';
plot(t.time,I_ins)
hold on
plot(t.time,xdq')
hold on
mean_Idq=mean(xdq')
HDEV_jmag.Idmean=mean_Idq(1);
HDEV_jmag.Iqmean=mean_Idq(2);
yline(mean_Idq)
hold on
text([mean(t.time(i))],[mean_Idq(1)],num2str(mean_Idq(1)))
hold on
text([mean(t.time(i))],[mean_Idq(2)],num2str(mean_Idq(2)))
formatter_sci

figure
plot(t.time,u_ins')


%% One elec period extract
HDEV_jmag=fcn_One_period_sampling(HDEV_jmag);
plot(HDEV_jmag.Iabc.time, HDEV_jmag.Iabc(:,1:3).Variables);

%% FFT - circuit
FFT_ia=fcn_fft_circuit(HDEV_jmag,HDEV_jmag.Iabc.Ia);
FFT_ib=fcn_fft_circuit(HDEV_jmag,HDEV_jmag.Iabc.Ib);
FFT_ic=fcn_fft_circuit(HDEV_jmag,HDEV_jmag.Iabc.Ic);

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

%% phasor diagram

%%
