%  init



% object make
HDEVdata=DataPkBetaMap(12);
[Ipk,beta]=meshgrid([0:50:750], [0:5:90]);

%% Import Measured Data
torque_map=readmatrix("Z:\01_Codes_Projects\git_Motor_System_Model\SKKU_RT\SKKU_LUT\torque_ipk_beta.csv"); % 국민대 맵데이터로부터 추출 
Vds_test=readmatrix("Z:\01_Codes_Projects\git_Motor_System_Model\SKKU_RT\SKKU_LUT\vd_ipk_beta.csv");
Vqs_test=readmatrix("Z:\01_Codes_Projects\git_Motor_System_Model\SKKU_RT\SKKU_LUT\vq_ipk_beta.csv");

HDEVdata.current=Ipk;
HDEVdata.beta=beta;
HDEVdata.torque_map=torque_map;
HDEVdata.voltage.Vd=Vds_test;
HDEVdata.voltage.Vq=Vqs_test;
%% Plot beta Torque 
HDEVdata.plot_xbeta(HDEVdata,'torque')

% preconditionss
figure
HDEVdata.plot_xbeta(HDEVdata,'voltage')


% load test data
load("Z:\01_Codes_Projects\git_fork_emach\tests\data\HDEV_DataPkBetaMap.mat")
formatter_sci
a=HDEVdata.current(19,16)
b=HDEVdata_test.current(19,16)
assert(a==b, "not same object data")