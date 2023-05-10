% TorquemapOPmap=importfile_csv('Copy_of_Torque_map_OP_map.csv')
% TorquemapOPmap=importfile_csv('Copy_of_Torque_map_OP_map.csv')
output_path='D:\NGV\Output\'
lut_path='D:\NGV\LUT\'
ToyotaPriusOPtorquespeedmap=importfile_csv(strcat(lut_path,'Toyota_Prius_OP_torque_speed_map.csv'));
ToyotaPriusspeedIdIq7507500=importfile_csv(strcat(lut_path,'Toyota_Prius_speed_Id_Iq_750_7500.csv'));
% force_map_idiq_map=importfile_csv('force_map_idiq_map.csv');
% force_map_idiq_map_8000rpm=importfile_csv('force_map_idiq_map_8000rpm.csv');


plot_handle(1) = subplot(3, 1, 1);

scatter(ToyotaPriusspeedIdIq7507500.VarName2,ToyotaPriusspeedIdIq7507500.VarName3, DisplayName='NVH Test OP idiq', MarkerFaceColor='black')
hold on
scatter(ToyotaPriusOPtorquespeedmap.IdA,ToyotaPriusOPtorquespeedmap.IqA,Marker='x',DisplayName='idiq map')
hold on
xlabel('Id[Apk]')
ylabel('Iq[Apk]')
scatter(forcemapidiqmap.e02*sqrt(2),forcemapidiqmap.e1*sqrt(2))
grid on
legend

plot_handle(2)  = subplot(3, 1, 2);  
scatter(ToyotaPriusspeedIdIq7507500.VarName1,ToyotaPriusspeedIdIq7507500.VarName3,displayname='NVH OP iq',MarkerEdgeColor='blue')
hold on
scatter(ToyotaPriusspeedIdIq7507500.VarName1,ToyotaPriusspeedIdIq7507500.VarName2,displayname='NVH OPid',MarkerEdgeColor='red')
xlabel('RPM')
ylabel('Current[Apk]')
legend
% ax=gca;
% ax.XLim=[1000 15000]
plot_handle(2).XLim=[1000 15000]

plot_handle(3)  = subplot(3, 1, 3);  
scatter(ToyotaPriusOPtorquespeedmap.nrpm,ToyotaPriusOPtorquespeedmap.T2Nm, DisplayName='OP map',MarkerEdgeColor='flat')
xlabel('RPM')
ylabel('Torque[Nm]')
  
hold on
scatter(TorquemapOPmap.e02,-TorquemapOPmap.e3,DisplayName='NHV OP',MarkerFaceColor='black')


plot_handle(3).XLim=[1000 15000]
legend
hold on
scatter(forcemapidiqmap.e03,forcemapidiqmap.e2)