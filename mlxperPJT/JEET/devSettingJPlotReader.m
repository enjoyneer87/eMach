% devSettingJplotReader
% % # 주석 처리된 예시, 실제 사용 시 주석 해제
setPythonEnv('jmag')
module_path = 'C:\Program Files\JMAG-Designer23.1\Tools\JPlotReader\samples\Python';
modulepath='C:\Program Files\JMAG-Designer23.1'
if count(py.sys.path, module_path) == 0
    insert(py.sys.path, int32(0), module_path);
    insert(py.sys.path, int32(0),modulepath);
end



% Python 모듈(mainJplotReader)을 가져옴
JplotReader = py.importlib.import_module();

% 이제 JplotReader 모듈을 사용할 수 있습니다.
app=callJmag;
jplot_file_path=app.GetProjectFolderPath;
dir(jplot_file_path)
postkey_id = 16001;


runPythonJplot(tempPath, 16001)
tempPath='\e10MS_ConductorModel~6\e10MS_ConductorModel_SCL_Load~13\Case1\'
tempPath='D:\KangDH\Thesis\e10\JMAG\MSConductorModel\e10MS_ConductorModel_REF.jfiles\e10MS_ConductorModel_REF~7\e10MS_ConductorModel_REF_Load~16\Case1\Designer.jplot'
jplot_file_path=fullfile(jplot_file_path,tempPath,"Designer.jplot")
JplotReader.main(jplot_file_path, postkey_id);  % main 함수를 호출
%% matlab 2024a에서 python 3.8 미지원으로 인해 vscode에서 실행

outputMatPath='Z:\01_Codes_Projects\git_Pyleecan_fork\output_data.mat'

AData=load(outputMatPath)

py.sys.path

terminate(pyenv)

% Python code input
pycode = [...
"C:\Program Files\JMAG-Designer23.1\Tools\JPlotReader\samples\Python\mainJplotReader.py D:\KangDH\Thesis\e10\JMAG\MSConductorModel\e10MS_ConductorModel_REF.jfiles\e10MS_ConductorModel_REF~7\e10MS_ConductorModel_REF_Load~16\Case1\Designer.jplot 16001"...
];

pyrunfile(pycode)