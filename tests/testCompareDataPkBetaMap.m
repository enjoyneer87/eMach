%  init

% object make
HDEVdata_Measured=DataPkBetaMap(12);
[Ipk,beta]=meshgrid([0:50:750], [0:5:90]);

%% Import Measured Data
torque_map=readmatrix("Z:\01_Codes_Projects\git_Motor_System_Model\SKKU_RT\SKKU_LUT\torque_ipk_beta.csv"); % 국민대 맵데이터로부터 추출 
Vds_test=readmatrix("Z:\01_Codes_Projects\git_Motor_System_Model\SKKU_RT\SKKU_LUT\vd_ipk_beta.csv");
Vqs_test=readmatrix("Z:\01_Codes_Projects\git_Motor_System_Model\SKKU_RT\SKKU_LUT\vq_ipk_beta.csv");

HDEVdata_Measured.current=Ipk(:,1:3:end);
HDEVdata_Measured.beta=beta(:,1:3:end);

HDEVdata_Measured.torque_map=torque_map(:,1:3:end);
size(HDEVdata_Measured.current)
size(beta)

% HDEVdata_Measured.current=Ipk;
% HDEVdata_Measured.beta=beta;
% HDEVdata_Measured.torque_map=torque_map
HDEVdata_Measured.voltage.Vd=Vds_test;
HDEVdata_Measured.voltage.Vq=Vqs_test;
%% Plot beta Torque 

HDEVdata_Measured.plot_xbeta(HDEVdata_Measured,'torque','scatter')


%% Import Motorcad Data
HDEV_motorcad=MotorcadData(12);
HDEV_motorcad.motocadLabPath='Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2\Lab'
HDEV_motorcad.proj_path=HDEV_motorcad.motorcadMotPath;
HDEV_motorcad.file_path=HDEV_motorcad.proj_path;
HDEV_motorcad.matfileFindList=what(HDEV_motorcad.motocadLabPath);
HDEV_motorcad.file_name='HDEV_Model2';
inputobj=HDEV_motorcad;

HDEV_motorcad.matfileFindList.mat
i=1
HDEVdata_Simulation=DataPkBetaMap(12);
HDEVdata_Simulation.MotorcadMat=load(HDEV_motorcad.matfileFindList.mat{i})

%% Import Simulated Electromagnetic Torque

HDEVdata_Simulation.torque_map=(HDEVdata_Simulation.MotorcadMat.Electromagnetic_Torque)'
HDEVdata_Simulation.current=(HDEVdata_Simulation.MotorcadMat.Stator_Current_Line_Peak)';
HDEVdata_Simulation.beta=(HDEVdata_Simulation.MotorcadMat.Phase_Advance)';

HDEVdata_Simulation.MotorcadMat=fcnCorrectShaftTorque(HDEVdata_Simulation.MotorcadMat)
HDEVdata_Simulation.torque_map=(HDEVdata_Simulation.MotorcadMat.T_S)'

HDEVdata_Simulation.current=HDEVdata_Simulation.current(:,1:3:end)
HDEVdata_Simulation.beta=HDEVdata_Simulation.beta(:,1:3:end)
HDEVdata_Simulation.torque_map=HDEVdata_Simulation.torque_map(:,1:3:end)

size(HDEVdata_Simulation.current)
size(HDEVdata_Simulation.torque_map)
size(HDEVdata_Simulation.beta)
HDEVdata_Simulation.plot_xbeta(HDEVdata_Simulation,'torque')
formatter_sci
% colormap(cmap);


%% Calculate Shaft torque from Loss and Saturation
