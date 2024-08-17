function loadJMAG_PWMInput(app)

%% jcir 전체 path 생성
fullPath = mfilename('fullpath');
[currentFolderPath, ~, ~] = fileparts(fullPath);

jcirName='PWM_CurrentControl.jcir';
jcirFilePath = fullfile(currentFolderPath, jcirName);

%% Load Circuit
% mkJmagImportCircuit(app,jcirFilePath)
Model=app.GetCurrentModel;
StudyObj=app.GetCurrentStudy;
currentCircuit=StudyObj.GetCircuit;
StudyObj.LoadCircuit(jcirFilePath)

end