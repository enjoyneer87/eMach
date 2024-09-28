

% ref 
% Result4MDPICheckMotorCADExportToolTemp
JMAGParentPath='D:\KangDH\Thesis\e10';
parentPath='F:\KDH\Thesis\JEET';
[motFileList,~]=getResultMotMatList(parentPath);
%% Plot AC Loss Map
% try Final function

filteredTable           = getMCADLabDataFromMotFile(motFileList{1});
originLabLinkTable      = reNameLabTable2LabLink(filteredTable);
MCADLinkTable           = originLabLinkTable;
plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable);
close all
% [TC]make Response Table


JPJTList            =findJPJTFiles(JMAGParentPath)';
R1List              =JPJTList(contains(JPJTList,'R1'));
R1PatternDList      =R1List(contains(R1List,'PatternD'));
R1PatternDList      =R1PatternDList(~contains(R1PatternDList,'4k'));

for projectIndex=1:len(R1PatternDList)
    app.Load(R1PatternDList{projectIndex})
    curStudyObj     =app.GetCurrentStudy;
    csvPath         =mkJMAGResponseTable(app,curStudyObj,'joule',BoolAllCases,'Total');
end
% load JMAG response table

detectImportOptions("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv","ReadVariableNames",true,"VariableNamesRow",1)
opts=detectImportOptions("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv","VariableNamesLine",1);
preview("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv",opts)

CSVList=findCSVFiles(pwd)';
% List4k=findCSVFiles(pwd)'
% List4k=List4k(contains(List4k,'4k'))
% List4k=List4k(contains(List4k,'case','IgnoreCase',true))

CSVList=CSVList(contains(CSVList,'Map'));
% CSVList=[CSVList;List4k]
for csvindex=1:len(CSVList)
    CSVList{csvindex,2}=readtable(CSVList{csvindex},opts);
    CSVList{csvindex,2}=removevars(CSVList{csvindex,2},'Var1');
end
% Respons CaseTable 2 MCADLinkTable (dqTable) Format


app=callJmag;
CurStudyObj=app.GetCurrentStudy;
CurStudyObj.GetName
sampleDTTable=getJMAGDesingTable(CurStudyObj)

MCADLinkvar  =MCADLinkTable.Properties.VariableNames
DTvarName    =sampleDTTable.Properties.VariableNames
IpkIndex     =contains(DTvarName,'Ipk')
IrmsIndex    =contains(DTvarName,'Irms')

PhIndex      =contains(DTvarName,'MCADPhase')
IsIndex      =contains(MCADLinkvar,'Is')
angIndex     =contains(MCADLinkvar,'Angle')

DTvarName(IpkIndex)   =MCADLinkvar(IsIndex)
DTvarName(PhIndex)    =MCADLinkvar(angIndex)

sampleDTTable.Properties.VariableNames=DTvarName


JMAGLinkTable=[convertCharCell2Numeric(sampleDTTable(:,IrmsIndex).Variables),convertCharCell2Numeric(sampleDTTable(:,PhIndex).Variables)];
JMAGLinkTable=array2table(JMAGLinkTable,"VariableNames",[MCADLinkvar(IsIndex),MCADLinkvar(angIndex)]);

JMAGLinkTable.Is=JMAGLinkTable.Is*sqrt(2)
% Make LabLinkTable [Revised 4 Kr]

Kr=2 
JMAGLinkTable=addvars(JMAGLinkTable,zeros(height(JMAGLinkTable),1),'NewVariableNames','TotalACLoss');
for csvindex=1:len(CSVList)
    JMAGLinkTable.TotalACLoss=CSVList{csvindex,2}.Variables'/1000;
    tempJMAGLinkTable=JMAGLinkTable;
    if contains(CSVList{csvindex,1},'SCL')
        tempJMAGLinkTable.Is=Kr*JMAGLinkTable.Is
    end
    CSVList{csvindex,3}=tempJMAGLinkTable;
end

% make plot List

% def Speed
CSVListsTable=cell2table(CSVList);
CSVListsTable.Properties.VariableNames={'CSV','ResTable','dqTable'}
BoolREF=contains(CSVListsTable.CSV,'REF')
REFTable=CSVListsTable(BoolREF,:)
SpeedList=extractBetween(REFTable.CSV,'Load','kMap')
speed=convertCharCell2Numeric(SpeedList);
REFTable=addvars(REFTable,speed,'NewVariableNames','speedK')
REFTable=sortrows(REFTable,'speedK')

BoolSCL=contains(CSVListsTable.CSV,'SCL')
SCLTable=CSVListsTable(BoolSCL,:)
SpeedList=extractBetween(SCLTable.CSV,'Load','kMap')
speed=convertCharCell2Numeric(SpeedList);
SCLTable=addvars(SCLTable,speed,'NewVariableNames','speedK')
SCLTable=sortrows(SCLTable,'speedK')
%

% save('SCLTableMapPerSpeed.mat','SCLTable')
% save('REFTableMapPerSpeed.mat','REFTable')

%% Rdc Scaling

% Rdc and RdcSCL
MotFilePath='D:\KangDH\Thesis\e10\SLFEA\e10_UserRemeshSLFEA.mot'
MotFilePath='F:\KDH\Thesis\JEET\e10\refModel\e10_UserRemesh.mot'
[BuildingData,filteredLabTable4Scaling]=getMCADData4ScalingFromMotFile(MotFilePath)
RdcREF=BuildingData.MotorCADGeo.ResistanceActivePart*1.673e-08/1.724E-08;
RdcSCLM=RdcREF/Kr^2;
RdcSCL=BuildingData.MotorCADGeo.ResistanceActivePart*1.673e-08/1.724E-08;
if RdcSCLM==RdcSCL
    save('Rdcactive.mat','RdcREF')
end
Kr=2
load('Rdcactive.mat')
RdcSCL=RdcREF./Kr.^2
RdcSCLM=RdcSCL;

% Fig1. Plot Total AC Loss Dq Map

load('SCLTableMapPerSpeed.mat')
load('REFTableMapPerSpeed.mat')
devSurfOnlyACLoss

% 


% Fig 2. Plot Per Speed - Same Saturation

PhaseAdvance= 45
tempIsrms=100;
close all
%%%% sub Report Plot
TableList={REFTable,SCLTable}
colorList={'b','g'};
subrpRPM_ACLoss_IpkPh


%%