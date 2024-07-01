mcad=callMCAD
%% 경로

jprojPath="Z:\Simulation\JMAGDev\e10JFT047FeedbackControl.jproj"
jprojPath="Z:\Simulation\JMAGDev\e10JFT047FeedbackControlCoil.jproj"

InitialStudyName='FullPyFeedBackLoss'

%% 1. Model Setting -

% Should Use Template? - No? Why?
% Winding Setting Type - First, in the JFT047 fashion
% Model - MCADe10
% DXF Import - From devJmagSettingV4InnerRotorCheck
% Material - MCAD Material Making//
% File 새로 (1. 셋팅을 하나씩, 2. setting 정보를 mat으로 가지고 있다가 입력) or Setting File로부터?
% testDXFPath="Z:\Simulation\LabProj2023Evaluation\EqualFillFactor\A1_60"

%% [export했으면 다음으로]export Coil

settingDXFTable=defMCADDXFExportSettingVariable('Stator',0);
testStatorDXFPath='Z:\Simulation\JEETACLossValid_e10_v23\refModel\e10_User_statorCoils.dxf';
settingDXFTable.CurrentValue(contains(settingDXFTable.AutomationName,'DXFFileName'))={testStatorDXFPath};
setMcadTableVariable(settingDXFTable,mcad)
mcad.GeometryExport()


%% Rotor
settingDXFTable=defMCADDXFExportSettingVariable('Rotor');
testRotorDXFPath='Z:\Simulation\JEETACLossValid_e10_v23\refModel\e10_User_Rotor.dxf'
settingDXFTable.CurrentValue(contains(settingDXFTable.AutomationName,'FileName'))={testRotorDXFPath};
setMcadTableVariable(settingDXFTable,mcad)
mcad.GeometryExport()


%%
dxfFiles = findDXFFiles('Z:\Simulation\JEETACLossValid_e10_v23\refModel')';


%% Syre Model 2 Dxf
load('Z:\01_Codes_Projects\Torino_syRe\motorExamples\mot_01.mat')
syreToDxf(motorModel.geo.stator,motorModel.geo.rotor,pwd,'refModel')
pathname=pwd
filename='refModel'
stator=motorModel.geo.stator
rotor=motorModel.geo.rotor

%% WriteDXF 주기모델로 자르기
entitiesStatorStruct = readDXF(testStatorDXFPath)
entitiesStatorStruct = arrayfun(@(x) setfield(x, 'layer', 'stator'), entitiesStatorStruct);
% StatrDxf = filterEntitiesByAngle(entitiesStatorStruct, 45);
StatrDxf.entities=entitiesStatorStruct
plotEntitiesStruct(StatrDxf)
NewtestStatorDXFPath=strsplit(testStatorDXFPath,'.')
NewtestStatorDXFPath=[NewtestStatorDXFPath{1},'Periodic','.dxf']
writeDXF(NewtestStatorDXFPath, StatrDxf)
% dxf.entities=table2struct(filtered_arcTable)
% plotEntitiesStruct(dxf)

%% RotorDXF
entitiesRotorStruct = readDXF(testRotorDXFPath)
entitiesRotorStruct = arrayfun(@(x) setfield(x, 'layer', 'rotor'), entitiesRotorStruct);
RotorDxf = filterEntitiesByAngle(entitiesRotorStruct, 45);
plotEntitiesStruct(RotorDxf)
NewtestRotorDXFPath=strsplit(testRotorDXFPath,'.')
NewtestRotorDXFPath=[NewtestRotorDXFPath{1},'Periodic','.dxf']

writeDXF(NewtestRotorDXFPath, RotorDxf)
%% JMAG 모델링
% DXFtool(testRotorDXFPath)
% dxfList2Import(1).dxfPath=testStatorDXFPath
% dxfList2Import(2).dxfPath=testRotorDXFPath
dxfList2Import=[]
dxfList2Import(1).dxfPath=NewtestStatorDXFPath  ;
dxfList2Import(2).dxfPath=NewtestRotorDXFPath   ;
app=callJmag
app.Show
Model=app.GetCurrentModel
ItemList={'Stator','Rotor'};
dxfList2Import(1).sketchName=ItemList{1};
dxfList2Import(2).sketchName=ItemList{2};


Model.RestoreCadLink()

geomApp=app.CreateGeometryEditor(0);

geomApp.Show
sketchs=ImportDXF2Geom(dxfList2Import,geomApp);

StatorGeomAssemTable    =getGeomSketchAssembleTable('Stator',geomApp);
RotorGeomAssembleTable  =getGeomSketchAssembleTable('Rotor',geomApp);

geomApp.Hide;
geomApp.Show
%% 정보 가져오기 -Arc/Line/Region별 정보가져오기 



% setGetGeomStatorNameNTable - Conductor Numbering

% selObj=StatorGeomAssemTable.ReferenceObj(end)
% distanceFromCenter=getDistanceFromZero(selObj,geomApp)
[StatorAssemRegionTable,StatorGeomArcTable]=setGetGeomStatorNameNTable(StatorGeomAssemTable,geomApp);
%% Rotor Table
RotorGeomArcTable          =getArcDataTable(RotorGeomAssembleTable,geomApp);
RotorAssemRegionTable      =getRegionItemDataTable(RotorGeomAssembleTable,'Rotor',geomApp);
RotorAssemRegionTable=allocateSubSketchList2AssemRegionTable(RotorGeomAssembleTable,RotorAssemRegionTable,geomApp);
RotorRegionTablePerType = detRotorRegionTablePerType(RotorAssemRegionTable);
runnerType=checkInnerOuterMotor(StatorGeomArcTable,RotorGeomArcTable);

% RotorAssemRegionTable=setGetGeomRotorNameNTable(RotorGeomAssembleTable,geomApp)
%% 1.1 Define MachineData
MotorCADGeo=tempDefMCADMachineData4Scaling(mcad)
MotorCADGeo.Pole_Number
MachineData=MotorCADGeo
CoilWindingInfo=defCoilWindingInfoStruct(MotorCADGeo)
MotorCADGeo.Area4Resistance


RotorOnePoleAngle=max(RotorGeomArcTable.EndVertexTabletheta);
% RotorOnePoleAngle=2*RotorOnePoleAngle
Poles       = 360/RotorOnePoleAngle;
PhaseNumber=3;
%% 1.1.1 Stator OneSlot Angle 알고리즘 고도화
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

%% SetGeomDesignTable
setGeomDesignTable('stack_length',MachineData.StatorLength,app);

Freq=rpm2freqE(1500,Poles/2)
mkDesignerEquation('Freq',num2str(Freq),Study)
[~,PhaseAdvance]=mcad.GetVariable('PhaseAdvance')
mkDesignerEquation('PhaseAdvance',num2str(PhaseAdvance),Study)

setGeomDesignTable('Freq',Freq,app);

setGeomDesignTable('SLOTS',slots,app);
setGeomDesignTable('POLES',Poles,app);
%% CircPattern
createCircPattern4StatorCore(MachineData,StatorAssemRegionTable,app)
createCircPattern4withInput(MachineData,StatorAssemRegionTable,'Area',app)
createCircPattern4withInput(MachineData,StatorAssemRegionTable,'Insulation',app)
createCircPattern4withInput(MachineData,StatorAssemRegionTable,'Conductor',app)
geomApp.Show


%% 2. Designer ImportGetPropertyTable

% Equation의 Ld,Lq값은 어떻게? 사전 해석?
app.SaveAs(jprojPath)
app.ImportDataFromGeometryEditor();
geomApp.SaveCurrent();
Model=app.GetCurrentModel
StudyName='Sin'

%% 2.4 [TC]Apply Template
%% Sin//
% app.GetModel(u"e10JFT047FeedbackControl_0").ApplyAnalysisTemplate(u"Custom/IPM_e10CoilSin", refarray, refarray2, False, False, False, refarray3, False, False, refarray4)
SinStudyObj=Model.GetStudy('Sin')
Study=SinStudyObj
% Model.CreateStudy('Transient2D',StudyName)
%$\ 2.1 Study 설정 get & Set

% Study=Model.GetStudy(StudyName)

propertiesTableWithValue=getJMagStudyProperties(Study)
Study.GetStudyProperties().SetValue('ModelThickness', MachineData.StatorLength)
% geomApp=app.CreateGeometryEditor(0);

%% 2.2 Designer Part Table
% isConductor=0  % conductor 임
PartStruct=getJMAGDesignerPartStruct(app);
%% 2.2.1 ConductorPartTable Sorting
ConductorPartTable=sortingConductorTableBySlot(PartStruct);
changeJMAGPartNameTable(ConductorPartTable,app);
%%[TC]
% PartDataStruct=devDesignerPartDataTable(MachineData,app,isConductor);
PartStruct=getEdgeVertexIdwithXYZCheck(PartStruct,app);   

PartTable=struct2table(PartStruct)
PartStructByType = convertJmagPartStructByType(PartStruct);

NewLayerTable=getMagnetizationEdgeFromLayerTable(PartStructByType.MagnetTable,app)

NewLayerTable=struct2table(NewLayerTable)

setMagnetMagnetizationbyRefEdge(NewLayerTable,app,'N42EH')

LayerTable = sortrows(PartTable,"Area","descend");


%% 2.3 Make Set
SlotConductorSetName="SlotConductor";
Model.GetSetList().CreatePartSet("SlotConductor")
Model.GetSetList().GetSet("SlotConductor").SetUpdateByRelation(false)
Model.GetSetList().GetSet("SlotConductor").SetMatcherType("MatchNames")
Model.GetSetList().GetSet("SlotConductor").SetParameter("style", "prefix")
Model.GetSetList().GetSet("SlotConductor").SetParameter("text", "Stator/Slot")
Model.GetSetList().GetSet("SlotConductor").Rebuild()

RotorSetName="Rotor"
Model.GetSetList().CreatePartSet(RotorSetName)
Model.GetSetList().GetSet(RotorSetName).SetMatcherType("MatchNames")
Model.GetSetList().GetSet(RotorSetName).SetParameter("style", "prefix")
Model.GetSetList().GetSet(RotorSetName).SetParameter("text", "Rotor")
Model.GetSetList().GetSet(RotorSetName).Rebuild()

%% 2.4.1 Circuit 
% mkJmag3phaseConductorSinCircuit(app)
mkJmag3phaseCoilSinCircuit(app)


%% 2.5 Condition Seeting
%% 2.5.1 Rotationaly Periodic Boundary 
setRPBoundaryCondition(SinStudyObj, StatorAssemRegionTable.distanceRFromCenter(1)/2);
%% 2.5.2 Motion 
%%PWM
RotConObj=PWMStudyObj.GetCondition('Rotation');
RotConObj.AddSetFromModel(RotorSetName,1);


RotConObj=SinStudyObj.GetCondition('RotorMotion');
RotConObj.IsValid
RotConObj.AddSetFromModel('Rotor', 0)
%==RotConObj.AddSet(Model.GetSetList().GetSet("Rotor"), 0)


%% 2.5.3 Conductor or Coil
% [TC] Winding Coil - From devJmagSettingFSCWInnerRotor

firstSlotWirePartsTable=getFirstSlotWirePartTableFromPartStruct(PartStruct);
CoilModel=app.GetCurrentModel;
StudyObj=CoilModel.GetStudy(0);
setWireRegion(StudyObj,firstSlotWirePartsTable,1);
% CoilWindingInfo=setWindingSetting(StudyObj,CoilWindingInfo);

%%[TB][Coil] Conductor Setting

% % MotorCAD Calc
% sigma=1/1.724E-08
% Area4Resistance=MotorCADGeo.Area4Resistance 
% S_wire=Area4Resistance
% SingleCoilAreaInSqm=sqmm2sqm(S_wire);
% R_phaseMCAD = devCalcRphase(sigma, mm2m(ArmatureMLT),1,N_turn,SingleCoilAreaInSqm,N_serial,N_parallel)
% 
% % JMAG Calc
% R_phaseJMAG=devJmagPhaseResistanceFromWindingSet(CoilWindingInfo,app)

% PartStruct                            = PartDataStruct.PartStruct                          ;         
% CenterVertexDesignerTable             = PartDataStruct.CenterVertexDesignerTable           ;                       
% MatchedVertexTable                    = PartDataStruct.MatchedVertexTable                  ;                               
% OutMostConductorEdgeDesignerTable     = PartDataStruct.OutMostConductorEdgeDesignerTable   ;                                       


%% 3. Mesh Setting
% Element Size

% conductor 
MeshControlObj=PWMStudyObj.GetMeshControl()
%meshTotalPropertyTable
meshTotalPropertyTable=MeshControlObj.GetPropertyTable
meshTotalPropertyTable=char2CategoricalPropertiesTable(meshTotalPropertyTable)

% MeshControl Condition
NumConditions=MeshControlObj.NumConditions

MeshCondtionTable=table()
for MeshConditionIndex=1:NumConditions
MeshCondtionObj=MeshControlObj.GetCondition(MeshConditionIndex-1);
MeshCondtionTable.MeshCondition(MeshConditionIndex)             =MeshCondtionObj;
MeshCondtionTable.CondtionType{MeshConditionIndex}              ={MeshCondtionObj.GetType}
MeshCondtionTable.Name{MeshConditionIndex}                      ={MeshCondtionObj.GetName}
MeshCondtionTable.MeshCondtionPropertyTable(MeshConditionIndex) ={char2CategoricalPropertiesTable(MeshCondtionObj.GetPropertyTable)}
MeshCondtionTable.Parts(MeshConditionIndex)                     ={MeshCondtionObj.GetParts};
end

% Conductor
MeshCondtionTable.MeshCondition(contains([MeshCondtionTable{:,'Name'}{:}],'Conductor')').AddSetFromModel(SlotConductorSetName,0)
% core

% Magnet
subConObj=MeshCondtionTable.MeshCondition(MeshConditionIndex).Add
% Barrier?

% Skin Dpeth

% MeshCondtionTable.MeshCondition(contains([MeshCondtionTable{:,'CondtionType'}{:}],'SkinDepth')').AddSetFromModel(SlotConductorSetName,0)

%% 4. Material
%% 4.1 Load Material in matlab
%% 4.1.1 Syre Type
load('Z:\01_Codes_Projects\Torino_syRe\motorExamples\mot_01.mat');
BLKLABELS.materials=char(...
    mat.Stator.MatName,...
    mat.Rotor.MatName,...
    'N52M',...
    'Copper'...
    );  
% 'Magnet Operating Temperature
if any(unique(Magnetxy(:,9)) ~= 0)
PMTemp = mat.LayerMag.temp.temp(1,1);%20 C
end
stator_mat1 = BLKLABELS.materials(1,:);
stator_mat = strcat(stator_mat1,'Customized');
%'# New BH-curve data based on SyRe library
property = material_properties_iron(stator_mat1);
property.Type='Syre';
% Set Core Material
% syreMatProperties=fieldnames(property);
% save('syreMatProperties','syreMatProperties');
load('Z:\01_Codes_Projects\git_fork_emach\tools\material\syreMatProperties.mat')
%% 4.1.2 MCAD Type
CorefileName="Z:\01_Codes_Projects\git_fork_emach\tools\NO18_1160.mdb";

SteelName='NO18-1160'
mcad.ExportSolidMaterial(CorefileName,SteelName)
NO18_1160=readMCADMaterialDBFile(CorefileName);
TotalData_NO18_1160=converMCADCoreMagnetTable2CellFormat(NO18_1160,SteelName);
TotalData_NO18_1160.BHValueTable
TotalData_NO18_1160.MaxwellLossTable
% MCADMatProperties=NO18_1160.AutomationName
% save('MCADMatProperties','MCADMatProperties');

% mat =load('Z:\01_Codes_Projects\git_fork_emach\tools\NO18_1160.mat');


%% 4.2 Create Material in JMAG
JDesigner=app;
createCustomMaterialJMAG(app,TotalData_NO18_1160,SteelName)

%% Set Conductor Material
%% Set Material
ConductorPartCell={PartStruct(contains({PartStruct(:).Name}','Conductor')).Name};
for PartIndex=1:height(ConductorPartTable)
PWMStudyObj.SetMaterialByName(ConductorPartCell{PartIndex},"Copper")
% PWMStudyObj.GetMaterial(ConductorPartCell{PartIndex}).SetValue("EddyCurrentCalculation", 1)
end

%% 'stator material
% stator_mat=BLKLABELS.materials(1,:);
% 'stator lanimation factor in %
stator_lamfactor=99.7;
% '#stator magnetic saturation factor in %
% stator_magSatfactor = 100;
% 'Electric conductivity of the stator
%Use Materials which contain Hysteresis Loops from stator: Yes(1) / No(0)
hysteresisloop_s=0; % 0= not use 
                    % 1=use
%Allow eddy current from stator : Yes(1) / No(0)
eddycurrent_s=0;    % 0= No eddy current 
                    % 1= Allow eddy current 
                    % 2= calculate distribution in steel plate 
stator_mat='NO18-1160';
setJMAGCoreMaterial(PWMStudyObj,'Stator/StatorCore',stator_mat,1,stator_lamfactor,hysteresisloop_s,eddycurrent_s)
%% 'Rotor Material
setJMAGCoreMaterial(PWMStudyObj,'Rotor/RotorCore',stator_mat,1,stator_lamfactor,hysteresisloop_s,eddycurrent_s)

%% 'MagNet Material

MagfileName="Z:\01_Codes_Projects\git_fork_emach\tools\N42EH.mdb";
% mcad.ExportSolidMaterial(MagfileName,'N42EH')
N42EH=readMCADMaterialDBFile(MagfileName);
% 
TotalDataN42EH=converMCADMagnetTable(N42EH);
TotalDataN42EH.MagnetTable
% 
% Table1=TotalDataN42EH.str4DataTablePerTemp.DataAtTemp140
% Table2=TotalDataN42EH.str4DataTablePerTemp.DataAtTemp200
%     [alpha(end+1), beta(end+1)] = computeMCADMagTempCoefficients(Table1,Table2)
% 
% alpha=[]
% beta=[]
% for i=1:length(fieldNames)-1
%     fieldName1=fieldNames{i};
%     fieldName2=fieldNames{end-(i-1)};
% 
%     table1=TotalDataN42EH.str4DataTablePerTemp.(fieldName1)
%     table2=TotalDataN42EH.str4DataTablePerTemp.(fieldName2)
%     [alpha(end+1), beta(end+1)] = computeMCADMagTempCoefficients(table1,table2)
% end

%% Set Material



%% [2] Scale Model
%% 1. e10 model 2 JMAG (완전 자동화는 아니지만 만들어져있음)
jprojPath="Z:\Simulation\JMAGDev\e10JFT047FeedbackControlCoil.jproj"

%% 2. AC Loss JMAG MODEL Scale Validation
    %% 2.1 geoAPP scale 
Model.RestoreCadLink()
geomApp=app.CreateGeometryEditor(0);
scaleJMAGGeom(geomApp)
Model.UpdateCadModel()

    %%[Skip] 2.2 app mesh scale


%% 2.3 부하 스터디를 찾아서, circuit의 Amplitude값이 stringvalue인지 value인지에 따라 2배하기
NumStudies=Model.NumStudies;
for StudyIndex=1:NumStudies
StudyName=Model.GetStudy(StudyIndex-1).GetName;
    if contains(StudyName,'load',IgnoreCase=true)&&contains(StudyName,'noload',IgnoreCase=true)
        StudyObj=Model.GetStudy(StudyName);
        CircuitCompObj=StudyObj.GetCircuit().GetComponent("CS1 copy");
        compPropertyTable=CircuitCompObj.GetPropertyTable;
        StringValueObj=CircuitCompObj.GetStringValue('Amplitude');
        if ~isempty(StringValueObj)
        CircuitCompObj.SetValue('Amplitude',['2*',StringValueObj])
        else
        ValueObj= CircuitCompObj.GetValue('Amplitude');
        CircuitCompObj.SetValue('Amplitude',ValueObj*2)
        end
    end
end
%%  Plot Result [MCAD > JMAG]
% [TC]MCAD Plot -plotMCADEmagCalc ,defMCADGraphName
 setGraphNameCellArray=defMCADGraphName()
setGraphName='FluxLinkageOCPh1'
setGraphName='FluxLinkageLoadPh'
graphIndex=5
% for graphIndex=1:length(setGraphNameCellArray)

FluxLinkageLoadPh=setGraphNameCellArray(contains(setGraphNameCellArray,setGraphName))
for graphIndex=5:6
    % setGraphName=setGraphNameCellArray{graphIndex}
%     if graphIndex~=1
%     formalGraphName=setGraphNameCellArray{graphIndex-1};
%     else
%     formalGraphName=[];
%     end
% if  ~strcmp(setGraphName(1:end-3),formalGraphName(1:end-3))
    % figure(graphIndex)
% end
for GraphIndex=1:3
ResultStructEmagCalc(GraphIndex)=plotMCADEmagCalc(FluxLinkageLoadPh{GraphIndex}, mcad);
hold on 
end
% AllResultDataStruct=cell2struct(tempGrName,'dataTable')


%% Jmag Plot

%% change Study Name with Model Name 4 DataSet

% Jproj=getJProjHier(app)
% Jproj=setJMagHierStudyName(app);

DataSetCellArray=getDataSetCellFromDataManagerWithName(app, 'flux','load');
Jproj=sort2TableFromJmagDataSetByHier(DataSetCellArray,app)

%% Split DataSet By Hier
Jproj.e10JFT047FeedbackControlCoil_2.load_Coil_of_e10JFT047FeedbackControlCoil_2.Coil_FluxLinkage.plot


exportFigure
% table2Plot=Jproj.e10JFT047FeedbackControlCoil_2.load_Coil_of_e10JFT047FeedbackControlCoil_2.Coil_FluxLinkage
hold on
for GraphIndex=1:3
plotTransientTable(ResultStructEmagCalc(GraphIndex).dataTable)
hold on 
end
% plotJMAGResultDataStruct(table2Plot)
% hold on
saveFigures2eps(pwd)
figurePath=''
%% Field Result Plot
mm2m(0.05541)

[pk,gamma]=dq2pkBeta(-150,190)
