%  type Lab Model interpolation type ( no rotor position vector) -1
%  pk/beta,2 dq
%  FEA calculation  = 3 rotor position - pk-beta 4 rotorposition dq
%  5 measured map data (1 or 2) - assume 3,4 are not derivable  from
%  voltage waveform
% 'Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2'

% measured - idiq  & ipk-beta 1or 2
% motorcad 1,2,3,4
%  init
torque_map=readmatrix("Z:\01_Codes_Projects\git_Motor_System_Model\SKKU_RT\SKKU_LUT\torque_ipk_beta.csv"); % 국민대 맵데이터로부터 추출 
[Ipk,beta]=meshgrid([0:50:750], [0:5:90]);
Input.Rs= 0.0067;   
Input.p=12;
rpm=1000;
% object make
HDEVdata=DataPkBetaMap(12);

% load()
% meshgrid
HDEVdata.current=Ipk;
HDEVdata.beta=beta;
HDEVdata.torque_map=torque_map;
%%currentVec 1D
% NcurrentVec=5
% currentMax=1000;
% currentVec=[0:currentMax/(NcurrentVec-1):currentMax]
% phaseMax=90;
% NphaseVec=6
% phaseVec=[0:phaseMax/(NphaseVec-1):phaseMax];



HDEVdata.phaseVec=phaseVec;
HDEVdata.currentVec=currentVec;
%
Vds_test=readmatrix("Z:\01_Codes_Projects\git_Motor_System_Model\SKKU_RT\SKKU_LUT\vd_ipk_beta.csv");
Vqs_test=readmatrix("Z:\01_Codes_Projects\git_Motor_System_Model\SKKU_RT\SKKU_LUT\vq_ipk_beta.csv");


HDEVdata.voltage.Vd=Vds_test;
HDEVdata.voltage.Vq=Vqs_test;
HDEVdata.voltage.Vabs=sqrt(Vqs_test.^2 + Vds_test.^2);
HDEVdata.rpm=rpm;
HDEVdata.p=Input.p;
HDEVdata.Rs=Input.Rs;

% HDEVdata.current_dq.Iq
% preconditionss
%2d style

HDEVdata.plot_xpkybeta('flux')
% HDEVdata.plot_xdyq(HDEVdata,'flux')
% HDEVdata.plot_xdyq(HDEVdata,'flux')

HDEVdata.plot_xdyq(HDEVdata,'voltage')
HDEVdata.plot_xdyq(HDEVdata,'torque')



%3d style



% end 

% from 4


% fcn 3 -> 4