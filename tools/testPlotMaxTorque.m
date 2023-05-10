%% emlab format
% filepath='Z:\01_Codes_Projects\Testdata_post\Total_Effy_skew_rework_HDEV.csv';
 filepath="Z:\01_Codes_Projects\Testdata_post\수소동력 65도 부분부하 효율 평균정리_V5.csv"

[dataTable, NameCell]=readDataFile(filepath,40);
% % 데이터 후처리 
% speedMeasArray=replaceSimilarData(dataTable.RPM);
speedMeasArray=replaceSimilarData(dataTable.("Dynamo 속도"));

% torqueMeasArray=replaceSimilarData(dataTable.Torque);
torqueMeasArray=replaceSimilarData(dataTable.("Dynamo 토크"));

[speedMeasArray, BorderTorque] = plotMaxTorque(speedMeasArray, torqueMeasArray);

powerMeasureArray=rpm2radsec(speedMeasArray).*BorderTorque/1000



%% MotorCAD Lab TN format 
path='Z:\Thesis\Optislang_Motorcad\Validation\HDEV_Model2Temp115\Lab'
matfileFindList=what(path)
i=1
matdata=load(fullfile(path,matfileFindList.mat{i}));
for machineMode=2:2
speedArray=replaceSimilarData(matdata.Speed(:,machineMode));
torqueArray=replaceSimilarData(matdata.Electromagnetic_Torque(:,machineMode));

[speedArray, BorderTorque] = plotMaxTorque(speedArray, torqueArray);
hold on
end

scatter(1700,1200,'x','DisplayName','OP1');
text(1700,1200-10,'OP1','FontName','Times New Roman')
scatter(1700,900,'x','DisplayName','OP2');
text(1700,900-10,'OP2','FontName','Times New Roman')

scatter(4000,380,'x','DisplayName','OP3');
text(4000,380-10,'OP3','FontName','Times New Roman')

powerCalcArray=calcPowerArray(speedArray,torqueArray);
powerLimitArray=min(powerCalcArray,240)
TorqueLimitArray=calInvPowerArray(speedArray,powerLimitArray)

plotMaxTorque(speedArray,TorqueLimitArray)
hold on
formatter_sci
a=gca
a.XLabel.String='Speed[RPM]';
a.YLabel.String='Torque[Nm]';