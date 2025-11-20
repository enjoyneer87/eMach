DXFPath=DXFPath'
%[text] 회전자 & 고정자 따로인 DXF 준비 
[mcad,pymotorcad]=callMCAD('pyMCAD')
mc = pymotorcad.MotorCAD(open_new_instance=false)
mc.
standard_regions = [
    mc. get_region("Rotor Pocket"),
    mc. get_region("RotorDuctFluidRegion_1"),
    mc. get_region("RotorDuctFluidRegion_2")
]

 RPocket=   mc. get_region("Rotor Pocket")
line=cell(RPocket.entities(1))
line{:}
%%

refPath="C:\Users\user\Downloads\e8_mobility.mot"
%% MotFileName
[refDIR,FileName,~]=fileparts(refPath)
% Conductor
PartName ='Stator'
settingDXFTable    =defMCADDXFExportSettingVariable(PartName);
testStatorDXFPath  =fullfile(refDIR,strcat(FileName,PartName,'_Origin.dxf'))
settingDXFTable.CurrentValue(contains(settingDXFTable.AutomationName,'FileName'))={testStatorDXFPath};
setMcadTableVariable(settingDXFTable,mcad)
mcad.GeometryExport()

PartName ='Rotor'
settingDXFTable    =defMCADDXFExportSettingVariable(PartName);
testRotorDXFPath   =fullfile(refDIR,strcat(FileName,PartName,'_Origin.dxf'))
settingDXFTable.CurrentValue(contains(settingDXFTable.AutomationName,'FileName'))={testRotorDXFPath};
setMcadTableVariable(settingDXFTable,mcad)
mcad.GeometryExport()
mcad
%[text] 
DXFPath=findDXFFiles(refDIR)
testStatorDXFPath='D:\Lucid_ver1.dxf'
testStatorDXFPath='G:\KangDH\LabProject2023BenchMarking\Lucid\Lucid_M_CAD_1335A_None_4paraModel.dxf'
testStatorDXFPath='G:\KangDH\LabProject2023BenchMarking\TeslaSPlaid\TeslaSPlaidDXF.dxf'
max_object_angle = getMaxObjectAngle(entitiesStatorStruct);
SlotNumber=getSlotNumberFromSlotAngle(max_object_angle);
entitiesStatorStruct        =readDXF(testStatorDXFPath)

DXFtool(testStatorDXFPath)
entitiesStatorStruct        =arrayfun(@(x) setfield(x, 'layer', 'stator'), entitiesStatorStruct);
SingleSlotAngle=15


StatrDxf                    =filterEntitiesByAngle(entitiesStatorStruct, SingleSlotAngle);
StatrDxf.entities           =entitiesStatorStruct
StatrDxf.divisions=200
plotEntitiesStruct(StatrDxf)
NewtestStatorDXFPath        =strrep(testStatorDXFPath,'Origin','');
[~,NewtestStatorDXFPath,~]  =fileparts(NewtestStatorDXFPath);
NewtestStatorDXFPath        =fullfile(refDIR,strcat(NewtestStatorDXFPath,'_Periodic','.dxf'))
writeDXF(NewtestStatorDXFPath, StatrDxf)
% rev1에서 회전자 dxf 수정함

matchedStr=getStrMatchedFromStrArray(DXFPath,'rotor')
DXFtool(matchedStr)

entitiesRotorStruct = readDXF(matchedStr)
entitiesRotorStruct = arrayfun(@(x) setfield(x, 'layer', 'rotor'), entitiesRotorStruct);

SinglePoleAngle=45


NewtestRotorDXFPath         =strrep(testRotorDXFPath,'Origin','');
[~,NewtestRotorDXFPath,~]   =fileparts(NewtestRotorDXFPath);
NewtestRotorDXFPath         =fullfile(refDIR,[NewtestRotorDXFPath,'_Periodic','.dxf']);
RotorDxf = filterEntitiesByAngle(entitiesRotorStruct, 45);

plotEntitiesStruct(RotorDxf)
% delete(dxfFiles{:})
writeDXF(NewtestRotorDXFPath, RotorDxf);
dxfFiles = findDXFFiles(refDIR)';



dxfFiles = findDXFFiles(refDIR)';

%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline"}
%---
