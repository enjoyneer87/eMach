mcad=callMCAD %[output:16661235]
ActiveXParameters = readMcadActiveX2Table("D:\KangDH\Emlab_emach\tools\motorCAD\ActiveXParameters_v2522.txt") %[output:47f4d30e] %[output:953efe4c]
a=dir(currentFilePath) %[output:2481c9db]

currentFilePath=getMCADFilePathCurrent(mcad)

MCADLinkTable=getMCADLabDataFromMotFile(currentFilePath)
originLabLinkTable      = reNameLabTable2LabLink(MCADLinkTable);

plotMultipleInterpSatuMapSubplots(@plotFitResult, originLabLinkTable)

Plot_idiq_table
%[text] Export DXF
mcad.export
[refDIR,FileName,~]=fileparts(currentFilePath);

PartName ='Stator'
settingDXFTable    =defMCADDXFExportSettingVariable(PartName);
testStatorDXFPath  =fullfile(refDIR,[FileName,PartName,'_Origin.dxf'])
settingDXFTable.CurrentValue(contains(settingDXFTable.AutomationName,'FileName'))={testStatorDXFPath};
setMcadTableVariable(settingDXFTable,mcad)
mcad.GeometryExport()
PartName ='Rotor'
settingDXFTable    =defMCADDXFExportSettingVariable(PartName);
testRotorDXFPath   =fullfile(refDIR,[FileName,PartName,'_Origin.dxf'])
settingDXFTable.CurrentValue(contains(settingDXFTable.AutomationName,'FileName'))={testRotorDXFPath};
setMcadTableVariable(settingDXFTable,mcad)
mcad.GeometryExport()

DXFtool('E:\KDH\Drone\AXI\AXI_5325_16GoldeLin_Origin.dxf')


entitiesStatorStruct        =readDXF(testStatorDXFPath)
entitiesStatorStruct        =arrayfun(@(x) setfield(x, 'layer', 'stator'), entitiesStatorStruct);
StatrDxf                    =filterEntitiesByAngle(entitiesStatorStruct, 45);
StatrDxf.entities           =entitiesStatorStruct
StatrDxf.divisions=200
plotEntitiesStruct(StatrDxf)
NewtestStatorDXFPath        =strrep(testStatorDXFPath,'Origin','');
[~,NewtestStatorDXFPath,~]  =fileparts(NewtestStatorDXFPath);
NewtestStatorDXFPath        =fullfile(refDIR,[NewtestStatorDXFPath,'_Periodic','.dxf'])
writeDXF(NewtestStatorDXFPath, StatrDxf)

dxfFiles = findDXFFiles(refDIR)';
entitiesRotorStruct = readDXF(dxfFiles{1})
entitiesRotorStruct = arrayfun(@(x) setfield(x, 'layer', 'rotor'), entitiesRotorStruct);
RotorDxf = filterEntitiesByAngle(entitiesRotorStruct, 22.5);
plotEntitiesStruct(RotorDxf)
%[text] Make Mot File Per Material
[a,b]=mcad.GetVariable('Material_Magnet')
mcad.SetVariable('Material_Magnet','N38UH')
currentFilePath=getMCADFilePathCurrent(mcad)
N38FilePath=strrep(currentFilePath,'.mot','_N38UH.mot')
mcad.SaveToFile(N38FilePath)
mcad.BuildModel_Lab



[refLABBuildData]=getMCADBuildingData(mcad(1));
refLABBuildData.MotorCADGeo.Ratio_Bore
scalingFactorStruct=defScalingFactor(1.2,1,2,4,2,4,2);
k_Axial   =scalingFactorStruct.k_Axial   ;
k_Radial  =scalingFactorStruct.k_Radial  ;
k_Winding =scalingFactorStruct.k_Winding ;  
% % scale
scalingFactorStruct.n_c =scalingFactorStruct.turns_per_coil;    
ScaledMachineData = SLScaleMachine(scalingFactorStruct,refLABBuildData.MotorCADGeo);
setMcadVariable(ScaledMachineData,mcad(1));


%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline"}
%---
%[output:16661235]
%   data: {"dataType":"textualVariable","outputData":{"name":"mcad","value":"\tCOM.motorcad_appautomation"}}
%---
%[output:47f4d30e]
%   data: {"dataType":"warning","outputData":{"text":"경고: 테이블에 대한 변수 이름을 생성하기 전에 파일의 열 제목이 유효한 MATLAB 식별자가 되도록 수정되었습니다. 원래 열 제목은 VariableDescriptions 속성에 저장되어 있습니다.\n원래 열 제목을 테이블 변수 이름으로 사용하려면 'VariableNamingRule'을 'preserve'로 설정하십시오."}}
%---
%[output:953efe4c]
%   data: {"dataType":"tabular","outputData":{"columnNames":["Number","Input_Output","AutomationName","Category","Units","CurrentValue","DefaultValue","Modified","DataType","Description"],"columns":10,"dataTypes":["double","categorical","cellstr","categorical","categorical","cellstr","cellstr","cellstr","categorical","cellstr"],"header":"13055×10 table","name":"ActiveXParameters","rows":13055,"type":"table","value":[["1","i\/p","'ScriptAutoRun'","Scripting_Options","<undefined>","'0'","'0'","''","integer","'Automatically run the script before or during analysis'"],["2","i\/p","'ScriptAutoRun_PythonClasses'","Scripting_Options","<undefined>","'0'","'0'","''","integer","'Automatically run the during analysis'"],["3","compatibility","'ScriptPythonFunctionType'","Scripting_Options","<undefined>","'0'","'0'","''","integer","'Run the script with new classes or old functions'"],["4","i\/p","'ScriptFileName'","Scripting_Options","<undefined>","'No File Selected'","'No File Selected'","''","OleStr","'The name of the script file'"],["5","i\/p","'ScriptLines'","Scripting","<undefined>","'0'","'0'","''","integer","'Number of lines in VB script'"],["6","i\/p","'Script'","Scripting","<undefined>","''","''","''","OleStr","'VB script'"],["7","i\/p","'ScriptLines_Python'","Python_Scripting","<undefined>","'1'","'0'","'yes'","integer","'Number of lines in Python script'"],["8","i\/p","'Python_Script'","Python_Scripting","<undefined>","''","''","'yes'","OleStr","'Python script'"],["9","persistent","'OwnerProcessID'","Scripting_Options","<undefined>","'0'","'0'","''","integer","'Process ID of the caller (if exists) of this instance of Motor-CAD'"],["10","persistent","'DisableSleep'","Scripting_Options","<undefined>","'False'","'False'","''","boolean","'When true Motor-CAD will not allow computer to sleep'"],["11","i\/p","'Full_Winding_Circuit_View'","Calc_Options","<undefined>","'False'","'False'","''","boolean","'When this is false then the only a reduced winding circuit is shown in circuit editor'"],["12","i\/p","'ScriptFileName_Python'","Scripting_Options","<undefined>","'No File Selected'","'No File Selected'","''","OleStr","'The name of the Python script file'"],["13","recommended","'Scripting_Engine'","Scripting_Options","<undefined>","'0'","'0'","''","integer","'Which Scripting Engine to use, Python (Default) or VBA'"],["14","i\/p","'TVent_Fan_Definition'","Through_Vent","<undefined>","'0'","'0'","''","integer","'The through ventilation fan definition'"]]}}
%---
%[output:2481c9db]
%   data: {"dataType":"error","outputData":{"errorType":"runtime","text":"'currentFilePath'은(는) 인식할 수 없는 함수 또는 변수입니다."}}
%---
