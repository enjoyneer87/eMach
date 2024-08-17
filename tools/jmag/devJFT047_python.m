

app=callJmag
Jmag=callJmag


% jtmplPath or ApplyAnalysisTemplate()
jtmplPath=''

% jft047="D:\KangDH\deVSimulation\JFT047\JFT047FeedbackControl\JFT047FeedbackControl\JFT047FeedbackControl-04.jproj"
jft047='Z:\Thesis\00_Theory_Prof\JFTZIP\JFT047FeedbackControl\JFT047FeedbackControl\JFT047FeedbackControl-04.jproj'
app.Load(jft047)
app.Show
JModel=app.GetCurrentModel
JModel.IsValid


JModel.ExportAnalysisTemplate()

Study=JModel.GetStudy(0)
Study.IsValid
StudyProp=Study.GetStudyProperties

jft047refStudyProp=defJMAG2DStudyPropertiesTable(StudyProp)
jft047refStudyProp=getJMagStudyPropertiesTableValue(jft047refStudyProp,StudyProp)


jft047refStudyProp.PropertiesName(contains(jft047refStudyProp.PropertiesName,'Vector'))
jft047refStudyProp.PropertiesName(strcmp(jft047refStudyProp.PropertiesName,'CurrentDensity'))
jft047refStudyProp.("PropertiesValue")(strcmp(jft047refStudyProp.PropertiesName,'CurrentDensity'))

jft047refStudyProp.("PropertiesValue")(contains(jft047refStudyProp.PropertiesName,'Vector'))
jft047refStudyProp.("PropertiesValue")(contains(jft047refStudyProp.PropertiesName,'Vector'))={[1]}
jft047refStudyProp.("PropertiesValue")(strcmp(jft047refStudyProp.PropertiesName,'CurrentDensity'))={[1]}


setJmagConditionPropertiesValue(jft047refStudyProp,StudyProp)
NumMaterials=Study.NumMaterials

for MatIndex=1:1
selMat=Study.GetMaterialByIndex(MatIndex-1)
selMat.IsValid
selMat.GetName
end

PartIDs=JModel.GetPartIDs()

PartStruct=getJMAGDesignerPartStruct(app)

for PartIds=1:length(PartStruct)
Study.GetMaterial(PartStruct(PartIds).partIndex).SetValue("OutputResult", 1)
end


%% 1. Model Setting -

% Should Use Template? - No? Why?




% Winding Setting Type - First, in the JFT047 fashion

% Model - MCADe10

% DXF Import - From devJmagSettingV4InnerRotorCheck
% Material - MCAD Material Making//
% File 새로 (1. 셋팅을 하나씩, 2. setting 정보를 mat으로 가지고 있다가 입력) or Setting File로부터?




% testDXFPath="Z:\Simulation\LabProj2023Evaluation\EqualFillFactor\A1_60"
testDXFPath='Z:\Simulation\JMAGDev'

dxfFiles = findDXFFiles(testDXFPath)'
testStatorDXFPath=dxfFiles{4}
testRotorDXFPath=dxfFiles{3}
DXFtool(testStatorDXFPath)
DXFtool(testRotorDXFPath)

dxfList2Import(1).dxfPath=testStatorDXFPath
dxfList2Import(2).dxfPath=testRotorDXFPath

app=callJmag
app.Show

ItemList={'Stator','Rotor'};
dxfList2Import(1).sketchName=ItemList{1};
dxfList2Import(2).sketchName=ItemList{2};

geomApp=app.CreateGeometryEditor(0);
geomApp.Show
sketchs=ImportDXF2Geom(dxfList2Import,geomApp);

StatorGeomAssemTable    =getGeomSketchAssembleTable('Stator',geomApp)
RotorGeomAssembleTable  =getGeomSketchAssembleTable('Rotor',geomApp)

geomApp.Hide;
% geomApp.Show
% 정보 가져오기 -Arc/Line/Region별 정보가져오기 
% Conductor Numbering

% selObj=StatorGeomAssemTable.ReferenceObj(end)
% distanceFromCenter=getDistanceFromZero(selObj,geomApp)
[StatorAssemRegionTable,StatorGeomArcTable]=setGetGeomStatorNameNTable(StatorGeomAssemTable,geomApp)

%% Rotor Table

RotorGeomArcTable          =getArcDataTable(RotorGeomAssembleTable,geomApp);

RotorAssemRegionTable      =getRegionItemDataTable(RotorGeomAssembleTable,'Rotor',geomApp)
RotorAssemRegionTable=allocateSubSketchList2AssemRegionTable(RotorGeomAssembleTable,RotorAssemRegionTable,geomApp);
RotorRegionTablePerType = detRotorRegionTablePerType(RotorAssemRegionTable)

runnerType=checkInnerOuterMotor(StatorGeomArcTable,RotorGeomArcTable)

RotorAssemRegionTable=setGetGeomRotorNameNTable(RotorGeomAssembleTable,geomApp)
%% Define MachineData

RotorOnePoleAngle=max(RotorGeomArcTable.EndVertexTabletheta);
% RotorOnePoleAngle=2*RotorOnePoleAngle
Poles       = 360/RotorOnePoleAngle;
PhaseNumber=3;
%% Stator OneSlot Angle 알고리즘 고도화
 StatorOneSlotAngle=findStatorOneSlotAngle(StatorGeomArcTable)
% NSPP
StatorOneSlotAngle=StatorOneSlotAngle
NSPP=RotorOnePoleAngle/StatorOneSlotAngle/PhaseNumber;
q=NSPP;
slots=NSPP*PhaseNumber*Poles;

%%[TF]
MachineData.Poles                 =Poles              ;   
MachineData.StatorOneSlotAngle    =StatorOneSlotAngle ;               
MachineData.PhaseNumber           =PhaseNumber        ;       
MachineData.NSPP                  =NSPP               ;   
MachineData.q                     =q                  ;
MachineData.slots                 =slots              ;   
MachineData.runnerType            =runnerType         ;
% MachineData.StatorLength=3953.801938;
% 
% app(1)= actxserver(strcat('Designer.Application.','222'));
% 
% MagModel=app(2).GetCurrentModel
% MagModel.IsValid
MachineData.StatorLength=130;

% SetGeomDesignTable
setGeomDesignTable('stack_length',MachineData.StatorLength,app);

setGeomDesignTable('SLOTS',slots,app);
setGeomDesignTable('POLES',Poles,app);
createCircPattern4StatorCore(MachineData,StatorAssemRegionTable,app)
createCircPattern4withInput(MachineData,StatorAssemRegionTable,'Area',app)
createCircPattern4withInput(MachineData,StatorAssemRegionTable,'Insulation',app)
createCircPattern4withInput(MachineData,StatorAssemRegionTable,'Conductor',app)


%% Designer Import

% Equation의 Ld,Lq값은 어떻게? 사전 해석?
app.ImportDataFromGeometryEditor();

StudyName='FullPyFeedBackLoss'
Model=app.GetCurrentModel
Model.CreateStudy('Transient2D',StudyName)
% Study 설정 get & Set
Study=Model.GetStudy(StudyName)

propertiesTableWithValue=getJMagStudyProperties(Study)
Study.GetStudyProperties().SetValue('ModelThickness', MachineData.StatorLength)


geomApp=app.CreateGeometryEditor(0);
geomApp.SaveCurrent();

%% 

isConductor=1  % conductor 임
% PartDataStruct=devDesignerPartDataTable(MachineData,app,isConductor);
PartStruct=getJMAGDesignerPartStruct(app)


PartStruct                            = PartDataStruct.PartStruct                          ;         
CenterVertexDesignerTable             = PartDataStruct.CenterVertexDesignerTable           ;                       
MatchedVertexTable                    = PartDataStruct.MatchedVertexTable                  ;                               
 % OutMostConductorEdgeDesignerTable     = PartDataStruct.OutMostConductorEdgeDesignerTable   ;                                       



%% Syre - Backward Compatibility - MotorCAd

 dispDep('Z:\01_Codes_Projects\Torino_syRe\syreExport\syre_JMAG\')
 
%% Analysis Template
% 
% 
% *app.ApplyAnalysisTemplate()* : Specifies the analysis template of the tool 
% box and associates the template with the CAD model. 
% 
% *Parameters*
%% 
% path
%% 
% Path of Analysis Template in Toolbox 
%% 
% partnames
%% 
% Name or index of the table defined with a link between parts in a template 
% and CAD model 
%% 
% setnames
%% 
% Name or index of the table defined with a link between sets in a template 
% and CAD model 
%% 
% renameParts
%% 
% True=1 : Rename part name to match part name of template
% 
% False=0 : Do not rename part name to match template 
%% 
% renameSets
%% 
% True=1 : Rename set name to match template
% 
% False=0 : Do not rename set name to match template 
%% 
% onlyAddExistedSets
%% 
% True=1 : only add sets existed in model
% 
% False=0 : add empty sets if they are not existed in model 
%% 
% refnames
%% 
% Name or index of the table defined with a link between refrence targets in 
% a template and CAD model 
%% 
% renameRefs
%% 
% True=1 : Rename reference target name to match template
% 
% False=0 : Do not rename reference target name to match template 
%% 
% onlyAddExistedRefs
%% 
% True=1 : only add reference targets existed in model
% 
% False=0 : add empty reference targets if they are not existed in model 
%% 
% equationnames
%% 
% Name or index of the table defined with a link between equations in a template 
% and CAD model
%% 
% *partnames*
% 
% 도구 상자의 분석 템플릿을 지정하고 템플릿을 CAD 모델과 연결합니다. (세트 포함). 
% 
% 1: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classSet.html 
% Set> name of a template (or group part name)
% 
% 2: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classPart.html 
% Part> index of a template (or part group index)
% 
% 3: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classPart.html 
% Part> type of a template (0: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classPart.html 
% Part>, 1: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classPart.html 
% Part> group)
% 
% 4: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classPart.html 
% Part> name (or part group name) of a CAD model that a template is applied
% 
% 5: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classPart.html 
% Part> index (or part group index) of a CAD model that a template is applied
% 
% 6: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classPart.html 
% Part> type (0: part, 1: part group) of a CAD model that a template is applied
% 
% 다음 명령은 부품 수(또는 부품 그룹 수)를 반복합니다.
% 
% 
% 
% *setnames*
% 
% Specify the following format when setting tables with the set names above.
% 
% 1: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classSet.html 
% Set> name of a template
% 
% 2: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classSet.html 
% Set> index of a template
% 
% 3: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classSet.html 
% Set> type of a template ("part","face","edge","vertex")
% 
% 4: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classSet.html 
% Set> name of a CAD model that a template is applied
% 
% 5: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classSet.html 
% Set> index of a CAD model that a template is applied.
% 
% 6: <mk:@MSITStore:C:\Program%20Files\JMAG-Designer23.1\Help\en\script-designer.chm::/classSet.html 
% Set> type of a CAD model that a template is applied ("part","face","edge","vertex")
% 
% The following repeats the number of sets 
% 
% 
% 
% 
% 
% *JModel.ImportAnalysisTemplate*: Imports an analysis template (*.jtmpl) and 
% links the template to a CAD model. 
% 
% 
% 
% *JModel.ImportAnalysisTemplateAuto():* Imports an analysis template (*.jtmpl) 
% and links template and CAD model (includes set). 

% app.CreateAnalysisTemplateParameter()

app.ApplyAnalysisTemplate()
JModel.ImportAnalysisTemplate(jtmplPath)
% Template gogo


%

%% 
%% Material


BandMaterial                ='Air'                  ;
ShaftMaterial               ='Air'                  ;
RotorCoreMaterial           ='Hypocore 0.125mm'     ;            

%Stator
Model.GetStudy(StudyName).SetMaterialByName('Stator/StatorCore', 'Hypocore 0.125mm')
StudyObj=Model.GetStudy(StudyName)

ConductorPartTable=sortingConductorTableBySlot(PartStruct)
changeJMAGPartNameTable(ConductorPartTable);


%% Import Circuit

C=mkJmagImportCircuit(app)

%% Set Condition


setJmagCondition()
% StudyObj.SetMaterial()
% Insulation Material

% Rotor
PartStruct=changeJMAGDesignerPartName4InnerRotor(PartStruct,app)

Model.GetStudy(StudyName).SetMaterialByName('Rotor/RotorCore', RotorCoreMaterial)
% Model.GetStudy(StudyName).SetMaterialByName('Magnet', 'BJMT_N52UH')
Model.GetStudy(StudyName).SetMaterialByName('Band',BandMaterial)
Model.GetStudy(StudyName).SetMaterialByName('Shaft',ShaftMaterial)


%% 1.1 JMAG Full 효율맵


%% 1.2 RT - 효율맵




MCAD=callMCAD