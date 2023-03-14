%% DispEfficiencyMap
% 
%% various EfficiencyMap format

% MotorAnalysis format
% filename = 'Z:\01_Codes_Projects\motoranalysis-pm_v1.1_matlab\SimFiles\Priu.mat';

% Katech csv
filepath="Z:\01_Codes_Projects\Testdata_post\수소동력 65도 부분부하 효율 평균정리_V5.csv"

% Emlab Code
% filepath='Z:\01_Codes_Projects\Testdata_post\Total_Effy_skew_rework_HDEV.csv'

% MotorCAD Mat
% filepath='Z:\Thesis\HDEV\02_MotorCAD\MOT\12P72S_N42EH_Maxis_Br_95pro_LScoil_11T_op1\Lab\MotorLAB_elecdata_650v_780a_65deg_MTPA_Lossf_st1_5.mat'
% load(filepath)

% Jmag format



% tempImportEffimapHDEV


%% Load file
[dataTable, NameCell]=readDataFile(filepath,40);

%% 정리 데이터 
speedMeasArray=replaceSimilarData(dataTable.(3));
torqueMeasArray=replaceSimilarData(dataTable.("Dynamo 토크"));
efficiencyMeasArray=dataTable.("모터 효율");

%     speedMeasArray=replaceSimilarData(dataTable.RPM)
%     torqueMeasArray=replaceSimilarData(dataTable.Torque);
%     efficiencyMeasArray=dataTable.Efficiency
    %% Measured Effimap Plot

%     figure(2)

%% Plot 

plotEfficiencyContour(speedMeasArray,torqueMeasArray,efficiencyMeasArray)


