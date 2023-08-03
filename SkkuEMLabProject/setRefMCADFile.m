function RefMCADInfo = setRefMCADFile(refMotFilePath, MagneticConditionVariable, LabConditionVariable, settedConductorData, mcad)
    % Dependency Check
    % findPNGFiles
    % copyPNGFilesToPNGFolder
    % setMcadVariable
    % If 'mcad' variable is not provided, create a new instance
    if nargin < 5
        mcad = actxserver('motorcad.appautomation');
    end
    RefMCADInfo = struct();
    mcad.LoadFromFile(refMotFilePath);

    %% 경로 설정
    parts           = strsplit(refMotFilePath, filesep);
    parentPath      = fullfile(parts{1:end-1});
    [~, previewPath]                = mcad.GetVariable('PreviewFolderLocation');

    %% 설정전 refFile Screen
    previewPNGList                  =findPNGFiles(previewPath);
    copyPNGFilesToPNGFolder(previewPNGList,parentPath);        
    %% 환경 설정
    mcad.SetVariable('MessageDisplayState', 2);         % 메세지창 제거 (에러 발생시에도 코드 동작 지속)
    mcad.SetVariable('GeometryParameterisation', 1);    % Ratio mode in Motor-CAD
    mcad.ClearModelBuild_Lab()  ;
    % mcad.ClearAllData()         ;
    % mcad.ClearMessageLog()      ;
    mcad.ClearExternalCircuit   ;
    mcad.RestoreCompatibilitySettings();

    %% Variable 설정
    setMcadVariable(MagneticConditionVariable, mcad);
    setMcadVariable(LabConditionVariable, mcad);
    setMcadVariable(settedConductorData, mcad);

    %% Info Return
    RefMCADInfo.MagneticConditionVariable   = MagneticConditionVariable;
    RefMCADInfo.LabConditionVariable        = LabConditionVariable;
    RefMCADInfo.settedConductorData         = settedConductorData;

    %% 설정후 refFile Screen
    RadialfileName                      = ['refFileRadial_', 'After', '.png'];  
    StatorWindingfileName               = ['refFileStatorWinding_', 'After', '.png'];
    mcad.SaveScreenToFile('Radial',          fullfile(parentPath, RadialfileName));
    mcad.SaveScreenToFile('StatorWinding',   fullfile(parentPath, StatorWindingfileName));           
    % getMcadStatorVariable()
    %% 저장
    mcad.SaveToFile(refMotFilePath);

    disp('**Matlab DOE Code Message -reference file setting done')

    % If 'mcad' variable was created inside this function, quit the instance
    if nargin < 5
        mcad.Quit();
    end
end
