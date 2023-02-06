function output_strc=Jmag_fcn_result_export(input,o_data_struct)
    mcad = actxserver('MotorCAD.AppAutomation');
    proj=strcat(input.file_path,'\',input.file_name,'.mot');
   %   파일이 켜져있지 않으면 파일명 읽어서 열기
    mcad.LoadFromFile(proj);
    % project File Path
    Read_file_path=strcat(input.file_path,'\',input.file_name);
%     %% Find Model& study Name
%     ModelName=jmag.GetCurrentModel.GetName()
%     StudyName=jmag.GetCurrentStudy.GetName()
%     Simulation.ModelName=ModelName;
%     Simulation.StudyName=StudyName;
%     % Check for New Results
%     jmag.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName).CheckForNewResults();
%     % for number_case
%     number_case= jmag.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName).GetDesignTable().NumCases()
%% Do Simulate if not done
% 
% invoke(mcad,'SetVariable','PeakCurrent',500);
% 
% [success,x]=invoke(mcad,'GetVariable','PeakCurrent');
% 
% 
% %% 
%% Model 단위 [Tobe]
% 
% %%study 단위에서
% for i=1:number_case
%     Hasresult=jmag.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName).CaseHasResult(number_case-1);
%     case_result=struct('number_case',i,'Hasresult',Hasresult);
%     check_case(number_case).result_exist=Hasresult;
%     check_case(number_case).caseno=number_case;
% end

%% dataset / datamanager()

jmag.SetCurrentStudy(StudyName)
data_names=jmag.GetDataManager().GetAllNames()
o_data_name='LineCurrent';
res=jmag_fcn_graph_export(o_data_name)

%array data
motorcad_fcn_graph_export

%value data
motorcad_fcn_result_export


output_strc=input
output_strc.res=res
% for i=1:length(data_names(TF))

end 


