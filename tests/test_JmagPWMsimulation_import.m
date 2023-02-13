% test 
global jmag_version
jmag_version='210'
jft047Data.jmag_version=jmag_version
jft047Data=JmagData(8);
jft047Data.jproj_path='Z:\Downloads\JFT047FeedbackControl';
jft047Data.file_name='JFT047FeedbackControl-04'
jft047Data.file_path=strcat(jft047Data.jproj_path,'\',jft047Data.file_name);
jmag=jft047Data.jmagCall()
% jft047Data.p=12;
jft047Data.Rs= 0.0067;   
% jft047Data.Input.p=12;
jft047Data.Vdc=650;
jft047Data.Vs_max=jft047Data.Vdc*(2/pi)*0.98 % dankai
jft047Data.Is_max=750;     %pk value

jft047Data.modelNumber=jmag.NumModels()
for modelnumber=1:jft047Data.modelNumber
    jft047Data.modelName{modelnumber}=jmag.GetModel(modelnumber-1).GetName()
end
    
%% data import
jft047Data.outputName{1}='LineCurrent'
jft047Data.outputName{2}='Torque'

jft047Data=jmagFcnResultExport(jft047Data)
Jmag_Current=readtable(jft047Data.res{1});
names=Jmag_Current.Properties.VariableNames
Coil1=Jmag_Current.(names{21})
Coil3=Jmag_Current.(names{22})
Coil2=Jmag_Current.(names{23})

% rpm define
jft047Data.test_rpm=1000;
jft047Data.plot_rpm=1000;


% time & degree -theta setting
t=Jmag_Current.TimeS;
theta=jft047Data.wr_plot*t;
deg_theta=rad2deg(theta);

%
I_ins=[Coil1 Coil3 Coil2]'
[xab,xdq]=dq_trans(I_ins,deg2rad(deg_theta)')
idavg_ins=mean(xdq(1,:))
iqavg_ins=mean(xdq(2,:))
ipk_ins=sqrt(idavg_ins.^2+iqavg_ins.^2)


plot(xdq')
hold on
plot(I_ins','LineWidth',2)

% jmag.GetModel().Get
% assert(angles(3) == 90,'Fundamental problem: rightTri not producing right triangle')
