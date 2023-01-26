% test 

HDEV=emlab_MachineData
HDEV.jproj_path='D:\KDH\Thesis\HDEV\01_JMAG\Jproject';
HDEV.file_name='12p72_HDEV_1st_year_RT_20201019'
HDEV.file_path=strcat(HDEV.jproj_path,'\',HDEV.file_name);
HDEV.jmag_version='210'
HDEV.Rs=0.0067
% HDEV.p=12;
HDEV.Rs= 0.0067;   
% HDEV.Input.p=12;
HDEV.Vdc=650;
HDEV.Vs_max=HDEV.Vdc*(2/pi)*0.98 % dankai
HDEV.Is_max=750;     %pk value

% preconditions
HDEV=Jmag_fcn_result_export(HDEV)



Jmag_Current=readtable(HDEV.res);
Jmag_Current.Coil1

% theta 
t=Jmag_Current.TimeS;
theta=HDEV.Wr_plot*t;
deg_theta=rad2deg(theta);

%
I_ins=[Jmag_Current.Coil1 Jmag_Current.Coil3 Jmag_Current.Coil2]'
[xab,xdq]=dq_trans(I_ins,deg2rad(deg_theta)')
idavg_ins=mean(xdq(1,:))
iqavg_ins=mean(xdq(2,:))
ipk_ins=sqrt(idavg_ins.^2+iqavg_ins.^2);


plot(xdq')
hold on
plot(I_ins','LineWidth',2)

% assert(angles(3) == 90,'Fundamental problem: rightTri not producing right triangle')
