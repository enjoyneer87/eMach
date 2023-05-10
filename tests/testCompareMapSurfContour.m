
%% load two Contour data (Map data)
% Katech csv
filepath="Z:\01_Codes_Projects\Testdata_post\수소동력 65도 부분부하 효율 평균정리_V5.csv"
[dataTable, NameCell]=readDataFile(filepath,40);
speedMeasArray=replaceSimilarData(dataTable.(3));
torqueMeasArray=replaceSimilarData(dataTable.("Dynamo 토크"));
efficiencyMeasArray=dataTable.("모터 효율");
efficiencyMeasArray=dataTable.("U상 전류");
contour1Measured=plotEfficiencyContour(speedMeasArray,torqueMeasArray,efficiencyMeasArray);
% Mootorcad Simulation
filepath='Z:\Thesis\HDEV\02_MotorCAD\backup\12P72S_N42EH_Br_95pro_11T_Fidelity_study\Lab\MotorLAB_elecdataTemp65.mat'
load(filepath,'Speed','Shaft_Torque','Efficiency','Shaft_Power','DC_Bus_Voltage','Stator_Current_Line_Peak','Stator_Current_Line_RMS')
contour2Simulation.x=Speed;
contour2Simulation.y=Shaft_Torque;
contour2Simulation.z=Efficiency;

%% Calculate Error (Call Compare Function)

errormap=fcnCompareMapContour(contour1Measured,contour2Simulation);


errormap.x1d = reshape(errormap.x, numel(errormap.x),1); % 1x6 array
errormap.y1d = reshape(errormap.y, numel(errormap.y),1); % 1x6 array
errormap.z1d = reshape(errormap.z, numel(errormap.z),1); % 1x6 array
size(errormap.x1d)

plotErrorContour(errormap.x1d,errormap.y1d,errormap.z1d);

cntrs = [-10:0.1:10 -10:0.1:round(max(max(errormap.z)))];
contourf(errormap.x,errormap.y,errormap.z, 'levels', 0.25, 'EdgeColor', 'none', 'DisplayName', 'Efficiency Contour');
hold on
contour3(errormap.x,errormap.y,errormap.z, cntrs,'EdgeColor', 'k', 'ShowText', 'on', 'TextStep', 2);

%% Patch Manual
    % TN line  추정 
[speedArray, BorderTorque] = plotMaxTorque(speedMeasArray,torqueMeasArray);
speedArray = speedArray';
BorderTorque = BorderTorque';
patch([speedArray speedArray(end) speedArray(1)], [BorderTorque 1.1*max(BorderTorque) 1.1*max(BorderTorque)], max(efficiencyMeasArray)*ones(1, length(BorderTorque)+2), [1 1 1]); 
hold on;

xlabel('Speed, [RPM]'); 
ylabel('Torque, [Nm]'); 
load('EffimapMeasureInfo.mat')
m1no=gca;
m1no.XLim=figInfo.xLim ;
m1no.YLim=figInfo.yLim ;
m1no.XTick= figInfo.xTick;
m1no.YTick= figInfo.yTick;
%   cellstr(get(gca,'XTickLabel'));=figInfo.xTickLabel
%   cellstr(get(gca,'YTickLabel'));=figInfo.yTickLabel
    formatter_sci;
m1no1=gcf;
m1no1.Position=figInfo.size;

