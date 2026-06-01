%% just load mat
load('SCLTableMapPerSpeed.mat');
load('REFTableMapPerSpeed.mat');
CSVList=[REFTable;SCLTable]
CSVList=table2cell(CSVList)
close all
Kr=2
load('Rdcactive.mat')

JMAGLinkTable=SCLTable.dqTable{1};

%% get From Current Jmag File

PortNumber=getPCRDPPortNumber
if PortNumber==38100
parentPath='F:\KDH\Thesis\JEET'
JMAGPath='D:\KangDH\Thesis\e10\JMAG'
elseif PortNumber==38002
parentPath='Z:\KDH\Thesis\JEET'
end


speed=[4000:4000:16000]
a=rpm2freqE(speed,4)

[motFileList,~]=getResultMotMatList(parentPath);
%% try Final function 
filteredTable           = getMCADLabDataFromMotFile(motFileList{1});
originLabLinkTable      = reNameLabTable2LabLink(filteredTable);
MCADLinkTable           = originLabLinkTable;
plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable);

app=callJmag;
JPJTList=findJPJTFiles(JMAGPath)'
R1List=JPJTList(contains(JPJTList,'Conductor'))
R1PatternDList=R1List(contains(R1List,'REF'))
for JPJTIndex=1:len(R1PatternDList)
    app.Load(R1PatternDList{JPJTIndex})
    Model=app.GetCurrentModel
    NumStudies=app.NumStudies;
    ResultCSVPath=cell(NumStudies,1);
    sampleDTTable=[];
    for StudyIndex=1:NumStudies     
        curStudyObj             =Model.GetStudy(StudyIndex-1);
        curStudyObj.CheckForNewResults;
        curStudyName            =curStudyObj.GetName;
        sampleDTTable{StudyIndex}          =getJMAGDesingTable(curStudyObj);
        Numcase=height(sampleDTTable);
        BoolHasResult=repmat(logical(0),Numcase,1);
        for caseIndex=1:Numcase
            if curStudyObj.CaseHasResult(caseIndex-1)
                BoolHasResult(caseIndex)=1;
            end
        end
        % if all(BoolHasResult)
        % ResultCSVPath{StudyIndex}=exportJMAGOnlyHasAllCaseTables(app,curStudyObj,'JEET');
        % end
    end
    % ResultCSVPath=removeEmptyCells(ResultCSVPath);
    if ~isempty(ResultCSVPath)
    R1PatternDList{JPJTIndex,3}=ResultCSVPath;
    R1PatternDList{JPJTIndex,4}=sampleDTTable;
    % R1PatternDList{JPJTIndex,2}=TotalTable;
    R1PatternDList{JPJTIndex,2}=app.GetProjectFolderPath;
    end
end

%% Make DT Table
MapDTTable=R1PatternDList{1,4}{1};
MCADLinkvar=MCADLinkTable.Properties.VariableNames
DTvarName=MapDTTable.Properties.VariableNames
IpkIndex=contains(DTvarName,'Ipk')
IrmsIndex=contains(DTvarName,'Irms')
PhIndex=contains(DTvarName,'MCADPhase')
IsIndex=contains(MCADLinkvar,'Is')
angIndex=contains(MCADLinkvar,'Angle')
DTvarName(IpkIndex)=MCADLinkvar(IsIndex)
DTvarName(PhIndex)=MCADLinkvar(angIndex)
MapDTTable.Properties.VariableNames=DTvarName
JMAGLinkTable=[convertCharCell2Numeric(MapDTTable(:,IrmsIndex).Variables),convertCharCell2Numeric(MapDTTable(:,PhIndex).Variables)];
JMAGLinkTable=array2table(JMAGLinkTable,"VariableNames",[MCADLinkvar(IsIndex),MCADLinkvar(angIndex)]);
JMAGLinkTable.Is=JMAGLinkTable.Is*sqrt(2);
