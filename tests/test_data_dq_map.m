%  init
torque_map=readmatrix("Z:\01_Codes_Projects\git_Motor_System_Model\SKKU_RT\SKKU_LUT\torque_ipk_beta.csv"); % 국민대 맵데이터로부터 추출 
[Ipk,beta]=meshgrid([0:50:750], [0:5:90]);
Input.Rs= 0.0067;   
Input.p=12;
rpm=1000;
% object make
HDEVdata=DataPkBetaMap(12);
HDEVdata.current=Ipk;
HDEVdata.beta=beta;
HDEVdata.torque_map=torque_map;

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

HDEVdata.plot_xdyq(HDEVdata,'flux')
HDEVdata.plot_xdyq(HDEVdata,'voltage')
HDEVdata.plot_xdyq(HDEVdata,'torque')



%3d style

