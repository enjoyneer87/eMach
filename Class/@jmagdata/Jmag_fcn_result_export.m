function output_strc=Jmag_fcn_result_export(input_obj)
    global ModelName
    global StudyName
        
    jmag = actxserver(strcat('designer.Application.',input_obj.jmag_version));
    jmag.Show()
%   path='Z:\Thesis\HDEV\Effy_map_JMAG_tool'
    jproj=strcat(input_obj.file_path,'.jproj');
    jmag.Load(jproj);   

    % Jproject File Path
    Read_file_path=jmag.GetProjectPath();
    % Project Name Setting
    jmag.SetProjectName(input_obj.file_name);
    pjt_name=jmag.GetProjectName();

    %   파일이 켜져있지 않으면 파일명 읽어서 열기

    %% Find Model& study Name
    ModelName=jmag.GetCurrentModel.GetName();
    StudyName=jmag.GetCurrentStudy.GetName();

    Simulation.ModelName=ModelName;
    Simulation.StudyName=StudyName;
% Check for New Results
    jmag.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName).CheckForNewResults();
% for number_case
    number_case= jmag.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName).GetDesignTable().NumCases();

%% Model 단위 [Tobe]

%%study 단위에서
for i=1:number_case
    Hasresult=jmag.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName).CaseHasResult(number_case-1);
    case_result=struct('number_case',i,'Hasresult',Hasresult);
    check_case(number_case).result_exist=Hasresult;
    check_case(number_case).caseno=number_case;
end

%% dataset / datamanager()
jmag.SetCurrentStudy(StudyName);
data_names=jmag.GetDataManager().GetAllNames();
celldisp(data_names);

for outputdata=2:length(input_obj.outputname)
idx=contains(data_names,input_obj.outputname{outputdata})
% idx=contains(data_names,o_data_name{2})
selected_data_name=data_names(idx)

%% Get array data
% o_data_name='LineCurrent'
% single_data_name=input_obj.outputname;
% extractBetween(data_names{1})

    % for i=1:length(selected_data_name)
    for i=1:4
    res=jmag_fcn_graph_export(selected_data_name{i},i,input_obj.outputname{outputdata});
    % jmag.GetModel(ModelName).GetStudy(StudyName).GetResultTable().GetDataFromName(typename,sourcename{1})
    
    %% Get value data
    
    
    % for i=1:length(data_names(TF))
    
    %% out 
    output_strc=input_obj;
    output_strc.res{1,i}={res};
    end
end

end 


