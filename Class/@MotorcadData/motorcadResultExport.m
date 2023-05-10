function output_strc=motorcadResultExport(input)
%% 가장 기초단위 eMag와 Thermal, Lab은 일단 추후
mcad = actxserver('MotorCAD.AppAutomation');
fullRefFileName=strcat(input.file_path,'\',input.file_name);
%   파일이 켜져있지 않으면 파일명 읽어서 열기
input.refFile=input.file_name;
mcad.LoadFromFile(strcat(fullRefFileName,'.mot'));
% project File Path

% Simul File
filename = strcat(fullRefFileName, 'ScriptRun');

%% Calculation Options

invoke(mcad, 'SetVariable', 'BackEMFCalculation', true);
invoke(mcad, 'SetVariable', 'CoggingTorqueCalculation', false);
invoke(mcad, 'SetVariable', 'ElectromagneticForcesCalc_OC', false);
invoke(mcad, 'SetVariable', 'TorqueSpeedCalculation', false);
invoke(mcad, 'SetVariable', 'DemagnetizationCalc', false);
invoke(mcad, 'SetVariable', 'ElectromagneticForcesCalc_Load', false);
invoke(mcad, 'SetVariable', 'InductanceCalc', false);
invoke(mcad, 'SetVariable', 'BPMShortCircuitCalc', false);
invoke(mcad, 'SetVariable', 'TorqueCalculation', false);


%% Mag Calculation Fidelity
OpenCircuitCalc = 1;
invoke(mcad, 'SetVariable','OpenCircuitCalc',OpenCircuitCalc);

%% Mag Calculation Fidelity
mcad.SetVariable('MagneticSolver',input.MagneticSolver)
mcad.SetVariable('ProximityLossModel',input.ProximityLossModel)

mcad.SetVariable('HybridACLossMethod',input.HybridACLossMethod)
mcad.SetVariable('LabModel_ACLoss_Method',input.LabModel_ACLoss_Method)

% factor 
mcad.SetVariable('StackingFactor_Magnetics',input.StackingFactor_Magnetics)
%% PointPer Cycle
PointsPerCycle = 120; % BackEMF
NumberCycles = 1; 
invoke(mcad, 'SetVariable', 'BackEMFPointsPerCycle', PointsPerCycle);
invoke(mcad, 'SetVariable', 'BackEMFNumberCycles', NumberCycles);

PointsPerCycle = 30; % Torque
invoke(mcad, 'SetVariable', 'TorquePointsPerCycle', PointsPerCycle);
invoke(mcad, 'SetVariable', 'TorqueNumberCycles', NumberCycles);

PointsPerCycle = 240; % Cogging
invoke(mcad, 'SetVariable', 'CoggingPointsPerCycle', PointsPerCycle);
invoke(mcad, 'SetVariable', 'CoggingNumberCycles', NumberCycles);

PointsPerCycle = 120; % Loss
invoke(mcad, 'SetVariable', 'CoreLossPointsPerCycle', PointsPerCycle);
invoke(mcad, 'SetVariable', 'CoreLossNumberCycles', NumberCycles);

%% Saving File
 
invoke(mcad,'SaveToFile', strcat(filename,'.mot'));


%% Do Simulate if not done
success = invoke(mcad,'DoMagneticCalculation');
if success == 0
    disp('Magnetic calculation successfully completed');
else
    disp('Magnetic calculation failed');
end
[success,x]=invoke(mcad,'GetVariable','PhysicalModelType')


%%  Export Point data to csv file

% 체크할 폴더 경로
folderPath = filename;

% 폴더가 존재하지 않으면 폴더 생성
if ~exist(folderPath, 'dir')
    mkdir(folderPath);
    fprintf('폴더 생성: %s\n', folderPath);
else
    fprintf('폴더가 이미 존재합니다: %s\n', folderPath);
end

exportFile = strcat(folderPath, '\Export_EMag_Results.csv');
success = invoke(mcad,'ExportResults', 'EMagnetic', exportFile);
if success == 0
    disp('Results successfully exported');
else
    disp('Results failed to export');
end



%% Model 단위 [Tobe]





%% dataset / datamanager()

% jmag.SetCurrentStudy(StudyName)
% data_names=jmag.GetDataManager().GetAllNames()
% o_data_name='LineCurrent';
% res=jmag_fcn_graph_export(o_data_name)
% 
% %array data
% motorcad_fcn_graph_export
% 
% %value data
% motorcad_fcn_result_export
% 
% 
output_strc=input
% output_strc.res=res
% % for i=1:length(data_names(TF))

end 


