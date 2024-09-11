% ref 
% Result4MDPICheckMotorCADExportToolTemp
parentPath='D:\KangDH\Thesis\e10\refModel'
[motFileList,~]=getResultMotMatList(parentPath);


%% try Final function 
filteredTable           =getMCADLabDataFromMotFile(motFileList{1});
originLabLinkTable      = reNameLabTable2LabLink(filteredTable);
MCADLinkTable           = originLabLinkTable;
plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable);


%% load JMAG response table
detectImportOptions("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv","ReadVariableNames",true,"VariableNamesRow",1)
opts=detectImportOptions("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv","VariableNamesLine",1)
preview("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv",opts)

CSVList=findCSVFiles(pwd)'
CSVList=CSVList(contains(CSVList,'Map'))

for csvindex=1:len(CSVList)
    CSVList{csvindex,2}=readtable(CSVList{csvindex},opts);
    CSVList{csvindex,2}=removevars(CSVList{csvindex,2},'Var1');
end

%% Respons CaseTable 2 MCADLinkTable (dqTable) Format 
app=callJmag
CurStudyObj=app.GetCurrentStudy
CurStudyObj.GetName
sampleDTTable=getJMAGDesingTable(CurStudyObj)

MCADLinkvar=MCADLinkTable.Properties.VariableNames
DTvarName=sampleDTTable.Properties.VariableNames
IpkIndex=contains(DTvarName,'Ipk')
IrmsIndex=contains(DTvarName,'Irms')

PhIndex=contains(DTvarName,'MCADPhase')

IsIndex=contains(MCADLinkvar,'Is')
angIndex=contains(MCADLinkvar,'Angle')

DTvarName(IpkIndex)=MCADLinkvar(IsIndex)
DTvarName(PhIndex)=MCADLinkvar(angIndex)

sampleDTTable.Properties.VariableNames=DTvarName


JMAGLinkTable=[convertCharCell2Numeric(sampleDTTable(:,IrmsIndex).Variables),convertCharCell2Numeric(sampleDTTable(:,PhIndex).Variables)];
JMAGLinkTable=array2table(JMAGLinkTable,"VariableNames",[MCADLinkvar(IsIndex),MCADLinkvar(angIndex)]);
JMAGLinkTable.Is=JMAGLinkTable.Is*sqrt(2)

%% Make LabLinkTable 
JMAGLinkTable=addvars(JMAGLinkTable,zeros(height(JMAGLinkTable),1),'NewVariableNames','TotalACLoss');
for csvindex=1:len(CSVList)
    JMAGLinkTable.TotalACLoss=CSVList{csvindex,2}.Variables';

    CSVList{csvindex,3}=JMAGLinkTable;
end

for csvindex=1:len(CSVList)
plotMultipleInterpSatuMapSubplots(@plotFitResult, CSVList{csvindex,3});
hold on
end
%% 3D AC Loss Surface
n=[1 2 3]
mergeFigures(4.*(n-1)+1)
n=[4 5 6]
mergeFigures(4.*(n-1)+1)

%% Plot Per Speed
CSVListsTable=cell2table(CSVList);

CSVListsTable.Properties.VariableNames={'CSV','ResTable','dqTable'}

REFTable=CSVListsTable(1:3,:)
SpeedList=extractBetween(REFTable.CSV,'Load','kMap')
speed=convertCharCell2Numeric(SpeedList);
REFTable=addvars(REFTable,speed,'NewVariableNames','speedK')
REFTable=sortrows(REFTable,'speedK')

SCLTable=CSVListsTable(4:6,:)
SpeedList=extractBetween(SCLTable.CSV,'Load','kMap')
speed=convertCharCell2Numeric(SpeedList);
SCLTable=addvars(SCLTable,speed,'NewVariableNames','speedK')
SCLTable=sortrows(SCLTable,'speedK')


for SpeedIndex=1:3    
    [ACFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(REFTable.dqTable{SpeedIndex},'TotalACLoss');
    [id,iq]=pkgamma2dq(460,43.3);
    ACperspeed(SpeedIndex)=ACFitResult(id,iq);
end
scatter([8000,12000,18000],ACperspeed)

%% Export J Contour
CurStudyObj=app.GetCurrentStudy;
for caseIndex=1:30
    CurStudyObj.SetCurrentCase(caseIndex-1)
    app.View().SetView("SL_Slot5Slot6")
    app.View().SetStep(138)
    app.ExportImageWithSize(['D:/KangDH/Thesis/e10/JMAG/SCL18kc', num2str(1), 'J.png'], 640, 480)
end

CurStudyObj=app.GetCurrentStudy;
for caseIndex=1:30
    CurStudyObj.SetCurrentCase(caseIndex-1)
    app.View().SetView("Slot5Slot6View")
    app.View().SetStep(138)
    app.ExportImageWithSize(['D:/KangDH/Thesis/e10/JMAG/REF18kc', num2str(1), 'J.png'], 640, 480)
end
%% export Slot J
app.View().SelectWorldPos(68.80333709716797, 45.77047348022461, 0, 1)
app.View().SelectWorldPos(70.5835952758789, 47.07881164550781, 0, 1)
app.View().SelectWorldPos(72.47284698486328, 48.3326416015625, 0, 1)
app.View().SelectWorldPos(73.76262664794922, 49.004981994628906, 0, 1)
parameter = app.GetCurrentStudy().CreateTableDefinition()
parameter.SetResultType(u"CurrentLossDensityScalar")
parameter.SetAllSteps()
parameter.SetIsShownMinMaxInfo(False)
parameter.SetIsShownPositionInfo(True)
app.GetCurrentStudy().ExportTable(parameter, u"D:/KangDH/Thesis/e10/JMAG/REF_18kc30JSlot5.csv", 0)
    