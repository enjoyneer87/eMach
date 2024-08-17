function jcirFilePath=mkJmag3phaseConductorSinCircuit(app)
Model=app.GetCurrentModel;
Study=app.GetCurrentStudy;
% currentCircuit=Study.GetCircuit;
% if ~currentCircuit.IsValid
% Study.CreateCircuit()
% Study.GetCircuit().CreateComponent("3PhaseCurrentSource", "CS1")
% Study.GetCircuit().CreateInstance("CS1", -29, 0)
% Study.GetCircuit().CreateComponent("WindingThreePhaseConductor", "Winding Three Phase Conductor1")
% Study.GetCircuit().CreateInstance("Winding Three Phase Conductor1", -25, -1)
% Study.GetCircuit().CreateComponent("Ground", "Ground")
% Study.GetCircuit().CreateInstance("Ground", -23, 0)
% else 
%     disp('This Study already has circuit.')
% end

fullPath = mfilename('fullpath');
   
 % 파일 경로에서 디렉토리, 파일 이름, 확장자를 분리합니다.
[currentFolderPath, ~, ~] = fileparts(fullPath);
 % .jcir 파일의 전체 경로를 만듭니다.
jcirFilePath = fullfile(currentFolderPath, 'FEM_conductor_Input_Sin.jcir');
Study.LoadCircuit(jcirFilePath)
end