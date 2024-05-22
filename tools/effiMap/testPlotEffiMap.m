%% DispEfficiencyMap

%% various EfficiencyMap format

% MotorAnalysis format
% filename = 'Z:\01_Codes_Projects\motoranalysis-pm_v1.1_matlab\SimFiles\Priu.mat';
% Katech csv (from tempImportEffimapHDEV)
filepath="Z:\01_Codes_Projects\Testdata_post\수소동력 65도 부분부하 효율 평균정리_V5.csv"

% Emlab Code
% filepath='Z:\01_Codes_Projects\Testdata_post\Total_Effy_skew_rework_HDEV.csv'
% Jmag format(TBD)

% MotorCAD Mat
    % filepath='Z:\Thesis\HDEV\02_MotorCAD\MOT\12P72S_N42EH_Maxis_Br_95pro_LScoil_11T_op1\Lab\MotorLAB_elecdata_650v_780a_65deg_MTPA_Lossf_st1_5.mat'
%     filepath='Z:\Thesis\HDEV\02_MotorCAD\backup\12P72S_N42EH_Br_95pro_11T_Fidelity_study\Lab\MotorLAB_elecdataTemp65.mat'
%     load(filepath)
    % load(filepath,'Speed','Shaft_Torque','Efficiency','Shaft_Power','DC_Bus_Voltage')
%     postMotorCADMatEffi(Speed, Shaft_Torque, Efficiency, Shaft_Power, DC_Bus_Voltage);


%% Load file
[dataTable, NameCell]=readDataFile(filepath,40); % partially working


%% extract speed, torque, efficiency from table

[dataTable,speedVarNames,speedVar]=findVariablebyName(dataTable,{'rpm' 'speed'});

[dataTable,torqueVarNames,torquevar]=findVariablebyName(dataTable,'torque');
torqueVarNames
torquevar=dataTable.(torqueVarNames{1})
[dataTable,effiVarNames,effiVar]=findVariablebyName(dataTable,'effi');


speedMeasArray=replaceSimilarData(speedVar);
torqueMeasArray=replaceSimilarData(torquevar);
efficiencyMeasArray=replaceSimilarData(effiVar);


    speedMeasArray=replaceSimilarData(dataTable.("Dynamo 속도"))

torqueMeasArray=replaceSimilarData(dataTable.("Dynamo 토크"));
efficiencyMeasArray=dataTable.("모터 효율");

    % speedMeasArray=replaceSimilarData(dataTable.RPM)
%     torqueMeasArray=replaceSimilarData(dataTable.Torque);
%     efficiencyMeasArray=dataTable.Efficiency



    %% Measured Effimap Plot

%     figure(2)

%% Plot 

contour1Measured=plotEfficiencyContour(speedMeasArray,torqueMeasArray,efficiencyMeasArray);
% saveFigureAxesInfo('EffimapMeasureInfo')
% plotEfficiencyContour(Speed,Shaft_Torque,Efficiency)
%% 
load('EffimapMeasureInfo.mat')
m1no=gca;
m1no.XLim=figInfo.xLim ;
m1no.YLim=figInfo.yLim ;
m1no.XTick= figInfo.xTick;
m1no.YTick= figInfo.yTick;
%   cellstr(get(gca,'XTickLabel'));=figInfo.xTickLabel
%   cellstr(get(gca,'YTickLabel'));=figInfo.yTickLabel
% m1no.XLabel=figInfo.xLabel;
% m1no.YLabel=figInfo.yLabel;
m1no1=gcf;
m1no1.Position=figInfo.size;

%% Test Motorcad Effimap
plot3(Shaft_Torque,Speed,Efficiency,'o')
contourf(Speed,Shaft_Torque,Efficiency);


cntrs = [92:2:96 96:0.25:round(max(max(Efficiency)))];
contour2Simulation.x=Speed;
contour2Simulation.y=Shaft_Torque;
contour2Simulation.z=Efficiency;
contourf(Speed, Shaft_Torque, Efficiency, 'levels', 0.25, 'EdgeColor', 'none', 'DisplayName', 'Efficiency Contour');
hold on
[C, h] = contour3(Speed, Shaft_Torque, Efficiency, cntrs, 'EdgeColor', 'k', 'ShowText', 'on', 'TextStep', 2);
    %% Plot 양식
    caxis([80 100])
    xlabel('Speed, [RPM]'); 
    ylabel('Torque, [Nm]'); 
    set(gcf, 'renderer', 'zbuffer');
    
    %colormap

    % 색상값 범위 설정
    cmin = 0;
    cmax = 1;
    
    % 컬러맵 생성
    n = 256;  % 색상 수
    cmap = jet(n);
    ind = round(1 + (n-1) * (cmax-cmin) / (cmax-cmin+eps));
    cmap = cmap(1:ind,:);
    % 적용 예시
    colormap(cmap)


    % Colorbar 위치 설정
        cb = colorbar('Location', 'eastoutside');
    cb.Label.String = 'Efficiency [%]';

    lg=legend('Efficiency Contour', 'Location', 'northeast');
    % Scientific notation formatter
    formatter_sci;
    view(0,90); % 시야각 조절

load('EffimapMeasureInfo.mat')
m1no=gca;
m1no.XLim=figInfo.xLim ;
m1no.YLim=figInfo.yLim ;
m1no.XTick= figInfo.xTick;
m1no.YTick= figInfo.yTick;
%   cellstr(get(gca,'XTickLabel'));=figInfo.xTickLabel
%   cellstr(get(gca,'YTickLabel'));=figInfo.yTickLabel

m1no1=gcf;
m1no1.Position=figInfo.size;