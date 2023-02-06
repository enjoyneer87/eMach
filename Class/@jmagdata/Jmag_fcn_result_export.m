function output_obj=Jmag_fcn_result_export(input_obj)
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
% data_names=jmag.GetDataManager().GetAllNames();
% celldisp(data_names);

% jmag.GetModel(ModelName).GetStudy(StudyName).GetResultTable().WriteAllTables("Z:\01_Codes_Projects\git_fork_emach\Class\allresult.csv","Time")

for Noutputdata=1:length(input_obj.outputname)
% idx=contains(data_names,input_obj.outputname{Noutputdata})
% idx=contains(data_names,o_data_name{2})
% selected_data_name=data_names(idx);

%% Get array data
% o_data_name='LineCurrent'
single_data_name=input_obj.outputname{Noutputdata};
res=jmag_fcn_graph_export(input_obj.outputname{Noutputdata});

% extractBetween(data_names{1})

%     for Nsourcename=1:length(selected_data_name)
%     res=jmag_fcn_graph_export(selected_data_name{Nsourcename},Nsourcename,input_obj.outputname{Noutputdata});
%     
    %% Get value data
    
    
    % for i=1:length(data_names(TF))
    
    %% out 
output_obj=input_obj;
output_obj.res=res;
%     end
end

end 


