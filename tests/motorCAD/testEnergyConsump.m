FixedTemp65=load('Z:\Thesis\Optislang_Motorcad\Validation\HDEV_Model2TempWhy\Lab\MotorLAB_drivecycledataFixedTemp65.mat');
FixedTemp130=load('Z:\Thesis\Optislang_Motorcad\Validation\HDEV_Model2TempWhy\Lab\MotorLAB_drivecycledataFixedTemp130.mat');

ClosedTemp=load('Z:\Thesis\Optislang_Motorcad\Validation\HDEV_Model2TempWhy\Lab\MotorLAB_drivecycledataClosedCoupled.mat');

%% Winding Temperature
plot(FixedTemp65.Time,FixedTemp65.Stator_Winding_Temp_Average,'b','DisplayName','Fixed Temperature')
hold on
plot(ClosedTemp.Time,ClosedTemp.Stator_Winding_Temp_Average,'r','DisplayName','2Way Coupled Temperature')
hold on
plot(FixedTemp130.Time,FixedTemp130.Stator_Winding_Temp_Average,'g','DisplayName','Fixed Temperature')

formatter_sci

ax=gca
ax.XLabel.String='Time[sec]'
ax.YLabel.String='Temperature[\circ C]'

ClosedTempNew=interpolTimeDurationStruct(ClosedTemp,FixedTemp65)
ClosedTempNew.Time
%% Plot

subplot(2,1,1)
% scatter(FixedTemp65.Time,FixedTemp65.Total_Loss,'b','DisplayName','Fixed Temperature=65\circ C')
% hold on
scatter(ClosedTemp.Time,ClosedTemp.Total_Loss,'x','r','DisplayName','2Way Coupled Temperature')
hold on
scatter(FixedTemp130.Time(2:end)+1,FixedTemp130.Total_Loss(2:end),'g','DisplayName','Fixed Temperature=130\circ C')
formatter_sci


total_energy130=calcEnergyConsump(FixedTemp130.Time,FixedTemp130.Total_Loss);
total_energy65=calcEnergyConsump(FixedTemp65.Time,FixedTemp65.Total_Loss);
total_energyClosed=calcEnergyConsump(ClosedTemp.Time,ClosedTemp.Total_Loss);
