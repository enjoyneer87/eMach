%% DispEfficiencyMap

%% various EfficiencyMap format
% Emlab Code
filepath='Z:\01_Codes_Projects\Testdata_post\Total_Effy_skew_rework_HDEV.csv'

%% Load file
[dataTable, NameCell]=readDataFile(filepath,40); % partially working

%% extract speed, torque, efficiency from table
[dataTable,speedVarNames,speedVar]=findVariablebyName(dataTable,{'rpm' 'speed'});
[dataTable,torqueVarNames,torquevar]=findVariablebyName(dataTable,'torque');
torqueVarNames
torquevar=dataTable.(torqueVarNames{1})
[dataTable,effiVarNames,effiVar]=findVariablebyName(dataTable,'effi');


%% change to array
speedMeasArray=replaceSimilarData(speedVar);
torqueMeasArray=replaceSimilarData(torquevar);
efficiencyMeasArray=replaceSimilarData(effiVar);


%% Plot 
contour1Measured=plotEfficiencyContour(speedMeasArray,torqueMeasArray,efficiencyMeasArray);
