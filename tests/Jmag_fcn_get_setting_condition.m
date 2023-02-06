function data=Jmag_fcn_get_setting_condition(input_strc,condition_name,valuename)
    global ModelName
    global StudyName

    jmag = actxserver(strcat('designer.Application.',input_strc.jmag_version));    jmag.Show()
%   path='Z:\Thesis\HDEV\Effy_map_JMAG_tool'
    jproj=strcat(input_strc.file_path,'.jproj');
    jmag.Load(jproj);   


    % Jproject File Path
    Read_file_path=jmag.GetProjectPath()
    % Project Name Setting
    jmag.SetProjectName(input_strc.file_name);
    pjt_name=jmag.GetProjectName()

    %   파일이 켜져있지 않으면 파일명 읽어서 열기

    % Value
    if valuename=='speed'
       valuename_jmag="AngularVelocity"; 
    end
    if condition_name=='motion' | condition_name=='Motion'
        condition_name='Motion'
    end
    %% Find Model& study Name
    ModelName=jmag.GetCurrentModel.GetName()
    StudyName=jmag.GetCurrentStudy.GetName()

    Simulation.ModelName=ModelName;
    Simulation.StudyName=StudyName;
% Check setting condition value
    data=jmag.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName).GetCondition(condition_name).GetValue(valuename_jmag)

% for number_case
    number_case= jmag.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName).GetDesignTable().NumCases()


end