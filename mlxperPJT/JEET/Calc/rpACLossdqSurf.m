%[text:tableOfContents]{"heading":"**紐⑹감**"}

% ref 
% Result4MDPICheckMotorCADExportToolTemp
JMAGParentPath='F:\KDH\KDH';
parentPath='F:\KDH\Thesis\JEET'
[motFileList,~]=getResultMotMatList(parentPath);
%%
%[text] %[text:anchor:H_4ADD3444] ## Plot AC Loss Map
%[text] %[text:anchor:H_283134E6] #### try Final function
filteredTable           =getMCADLabDataFromMotFile(motFileList{2});
originLabLinkTable      = reNameLabTable2LabLink(filteredTable);
MCADLinkTable           = originLabLinkTable;
FitResultStr=plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable,'bilinear');
close all
%[text] ## RBF
%%

[IdGrid, IqGrid] = meshgrid(linspace(-300, 300, 6), linspace(0, 300, 5));
zData = sin(pi*IdGrid/600) .* cos(pi*IqGrid/300);
IdVec = IdGrid(:); IqVec = IqGrid(:); zVec = zData(:);

[rbfFunc, weights, coeffs, centers] = trainRBFThinplate(IdVec, IqVec, zVec);

% ?됯? 諛??쒓컖??[IdFine, IqFine] = meshgrid(linspace(-300,300,100), linspace(0,300,100));
zhat = rbfFunc(IdFine, IqFine);

figure;
surf(IdFine, IqFine, zhat);
title('Explicit TPS-RBF Fitting');
xlabel('Id'); ylabel('Iq'); zlabel('z');
shading interp; view(45, 30);

%%
%[text] %[text:anchor:H_479E9A10] #### \[TC\]make Response Table
app=callJmag

JPJTList=findJPJTFiles(JMAGParentPath)'
R1List=JPJTList(contains(JPJTList,'16k'))
R1PatternDList=R1List(contains(R1List,'PatternD'))
R1PatternDList=R1PatternDList(~contains(R1PatternDList,'4k'))
R1PatternDList=R1PatternDList(~contains(R1PatternDList,'NoEnd'))
R1PatternDList=R1PatternDList(contains(R1PatternDList,'Map'))

for projectIndex=1:len(R1PatternDList)
    app.load(R1PatternDList{projectIndex})
    curStudyObj=app.GetCurrentStudy
    csvPath=mkJMAGResponseTable(app,curStudyObj,'joule',BoolAllCases,'Total')
end
%[text] %[text:anchor:H_DE45473C] #### load JMAG response table
detectImportOptions("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv","ReadVariableNames",true,"VariableNamesRow",1)
opts=detectImportOptions("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv","VariableNamesLine",1)
preview("SCL_e10_WTPM_PatternD_R1_Load8kMap.csv",opts)

% 'From38100SCL_FPShiftAVGDiffMu_Joule_Loss'
CSVList=findCSVFiles(pwd)'
% List4k=findCSVFiles(pwd)'
% List4k=List4k(contains(List4k,'4k'))
% List4k=List4k(contains(List4k,'case','IgnoreCase',true))
% CSVList=CSVList(contains(CSVList,'Joule')&contains(CSVList,'FP'))

CSVList=CSVList(contains(CSVList,'JLoss'))

% CSVList=[CSVList;List4k]
for csvindex=1:len(CSVList)
    CSVList{csvindex,2}=readtable(CSVList{csvindex},opts);
    if ~contains(CSVList{csvindex},'FP')
    CSVList{csvindex,2}=removevars(CSVList{csvindex,2},'Var1');
    tempNonFPcsvIndex=csvindex;
    
    else
        PartNameList=CSVList{csvindex,2}.Properties.VariableNames;
        FreqList=convertCharCell2Numeric(CSVList{csvindex,2}.Frequency_Hz);
        rpmList =freqE2rpm(FreqList,polePair);
        CSVList{csvindex,2}=CSVList{csvindex,2}(:,PartNameList(contains(PartNameList,'Total')));
        FQTotalACLoss=CSVList{csvindex,2}.Variables;
        FQTotalACLoss=strrep(FQTotalACLoss,'"','');
        FQTotalACLossArray=convertCharCell2Numeric(FQTotalACLoss);
        for addIdx=1:len(rpmList)
            CSVList{end+1,1}=insertBefore(CSVList{csvindex,1},'.csv',['_Load',num2str(rpmList(addIdx)/1000),'kMap_']);
            CSVList{end,2}  =CSVList{tempNonFPcsvIndex,2};
            CSVList{end,2}.Variables=FQTotalACLossArray(addIdx,:);
        end
        CSVList(csvindex,:)=[];
    end
end


%%
%[text] %[text:anchor:H_CD2B5E2B] #### Respons CaseTable 2 MCADLinkTable (dqTable) Format

app=callJmag
CurStudyObj=app.GetCurrentStudy
CurStudyObj.GetName
sampleDTTable=getJMAGDesingTable(CurStudyObj)
polePair=convertCharCell2Numeric(unique(sampleDTTable.("Equation parameters: POLES")))/2;
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
%%
%[text] %[text:anchor:H_3B245612] #### Make LabLinkTable \[Revised 4 Kr\]
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

   
%%
%[text] %[text:anchor:H_0E08B038] #### make plot List
% def Speed
CSVListsTable=cell2table(CSVList);
CSVListsTable.Properties.VariableNames={'CSV','ResTable','dqTable'}
BoolFP=~contains(CSVListsTable.CSV,'FP')
BoolREF=contains(CSVListsTable.CSV,'REF')
REFTable=CSVListsTable(BoolREF&BoolFP,:)
SpeedList=extractBetween(REFTable.CSV,'Load','kMap')
speed=convertCharCell2Numeric(SpeedList);
REFTable=addvars(REFTable,speed,'NewVariableNames','speedK')
REFTable=sortrows(REFTable,'speedK')

BoolSCL=contains(CSVListsTable.CSV,'SCL')
SCLTable=CSVListsTable(BoolSCL&BoolFP,:)
SpeedList=extractBetween(SCLTable.CSV,'Load','kMap')
speed=convertCharCell2Numeric(SpeedList);
SCLTable=addvars(SCLTable,speed,'NewVariableNames','speedK')
SCLTable=sortrows(SCLTable,'speedK')
%
BoolSCL=contains(CSVListsTable.CSV,'SCL')
SCLFqTable=CSVListsTable(BoolSCL&~BoolFP,:)
SpeedList=extractBetween(SCLFqTable.CSV,'Load','kMap')
speed=convertCharCell2Numeric(SpeedList);
SCLFqTable=addvars(SCLFqTable,speed,'NewVariableNames','speedK')
SCLFqTable=sortrows(SCLFqTable,'speedK')



save('SCLTableMapPerSpeed.mat','SCLTable')
save('REFTableMapPerSpeed.mat','REFTable')
save('SCLFPFQTableMapPerSpeed.mat','SCLFqTable')

%%
%[text] %[text:anchor:H_50A49214] ## Rdc Scaling
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

%%
%[text] %[text:anchor:H_FB92B94D] ### Fig1. Plot Total AC Loss Dq Map
devSurfOnlyACLoss
%%
%[text] %[text:anchor:H_1E6389B8] #### 

%%
%[text] %[text:anchor:H_B49B9A93] ### Fig 2. Plot Per Speed - Same Saturation
PhaseAdvance= 45
tempIsrms=100;
close all
%%%% sub Report Plot
TableList={REFTable,SCLTable}
colorList={'b','g'}
subrpRPM_ACLoss_IpkPh


%[text] %[text:anchor:H_DD803652] ## 

%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline","rightPanelPercent":40}
%---

