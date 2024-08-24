% Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\deve10_JMAG_MS_ACLoss.m
% dev10MQSplotAC
e10MQS_WireTemplate_38100 % 실행해서 JMAG파일 만들기

PJTName='MQS';
ResultFilePath=findCSVFiles(pwd);
ResultFilePath=ResultFilePath(contains(ResultFilePath,PJTName,"IgnoreCase",true));
AppNumStudies=length(ResultFilePath);
for AppStudyIndex=1:AppNumStudies
    opts=delimitedTextImportOptions('NumVariables',1000);
    if exist(ResultFilePath{AppStudyIndex},"file")
    resultTableCell{AppStudyIndex,1}=readtable(ResultFilePath{AppStudyIndex},opts);
    resultTableCell{AppStudyIndex,2}=ResultFilePath{AppStudyIndex};
    end
end

%%  Get All Data
BoolLoad=contains(resultTableCell(:,2),'_Load','IgnoreCase',true);
BoolRef =contains(resultTableCell(:,2),'ref','IgnoreCase',true);
AppStudyIndex =(BoolRef&BoolLoad);
MQSRefLoadTable = parseJMAGResultTable(resultTableCell{AppStudyIndex,1});
MQSRefLoadTable.Properties.Description=resultTableCell{AppStudyIndex,2};

AppStudyIndex =(~BoolRef&BoolLoad);
MQSSCLoadTable = parseJMAGResultTable(resultTableCell{AppStudyIndex,1});
MQSSCLoadTable.Properties.Description=resultTableCell{AppStudyIndex,2};
TargetTable=MQSSCLoadTable;

% TablesCellCaseRowDataCol - 전체 결과 Waveform
%% ref
PhaseNumber=3;
RefPhaseActResistance=0.007;
refDCLoss=(650.5/sqrt(2)).^2*PhaseNumber*RefPhaseActResistance
MCAD=callMCAD
CurrentMotFilePath=getCurrentMotFilePath(MCAD)
[SCMachine,filteredLabTable4Scaling]=getMCADData4ScalingFromMotFile(CurrentMotFilePath)

SCPhaseActResistance=SCMachine.MotorCADGeo.ResistanceActivePart
SCDCLoss=(2*650.5/sqrt(2)).^2*PhaseNumber*SCPhaseActResistance;

%% Speed List
close all
% Average - along last 120Step (Total)
targetName='Total';
speedList=[1000:2000:15000];
TotalJoule4Case=cell(length(speedList),1);
for TableIndex=2:2
    for caseIndex=1:height(MQSRefLoadTable)
    speed2Plot=speedList(caseIndex);    
    table2Plot=MQSRefLoadTable{caseIndex,TableIndex}{1};
    varNames=table2Plot.Properties.VariableNames;
        if any(contains(varNames,targetName,"IgnoreCase",true))
        % calc
        table2plotPerVarNames=table2Plot(:,varNames);
        JouleAvgTablCell4Case{caseIndex,1}=varfun(@mean ,table2plotPerVarNames(end-120:end,:),"OutputFormat","table");
        JouleAvgTablCell4Case{caseIndex,2}=JouleAvgTablCell4Case{caseIndex,1}(:,end).Variables;
        end
    end
end


% plot 양식
% figure
yyaxis left
% LossLine(1)=plot(speedList,[JouleAvgTablCell4Case{:,2}]/1000,'*-')
hold on
refACLoss=[JouleAvgTablCell4Case{:,2}]/1000-refDCLoss/1000;
LossLine(1)=plot(speedList,refACLoss,'*-');
xlabel('Rotor Speed[RPM]')
ylabel('Total AC Loss[kW]')
LossLine(1).Color='K';

formatterFigure4Paper(2, '1x1')
hold on
% MQS SC 
% Average - along last 120Step (Total)
targetName='Total'
speedList=[1000:2000:15000];
TotalJoule4Case=cell(length(speedList),1);
for TableIndex=2:2
    for caseIndex=1:height(TargetTable)
    speed2Plot=speedList(caseIndex);    
    table2Plot=TargetTable{caseIndex,TableIndex}{1};
    varNames=table2Plot.Properties.VariableNames;
        if any(contains(varNames,targetName,"IgnoreCase",true))
        % calc
        table2plotPerVarNames=table2Plot(:,varNames);
        SCJouleAvgTablCell4Case{caseIndex,1}=varfun(@mean ,table2plotPerVarNames(end-120:end,:),"OutputFormat","table");
        SCJouleAvgTablCell4Case{caseIndex,2}=SCJouleAvgTablCell4Case{caseIndex,1}(:,end).Variables;
        end
    end
end
yyaxis left
SCACLoss=[SCJouleAvgTablCell4Case{:,2}]/1000-SCDCLoss/1000;
LossLine(2)=plot(speedList,SCACLoss,'^-')
xlabel('Rotor Speed[RPM]')
ylabel('Total AC Loss[kW]')
LossLine(2).Color='K'

yyaxis right
Ratio=plot(speedList,SCACLoss./refACLoss,'--');
ylabel('Ratio SC/Ref')
Ratio.Color='r';


%% Wave form B / LOSS/Current Density
% B,W Graph=AnalysisType(2)*DataType(2)* 2(Load) * 2(Model) *2(Layer-4,3 Layer) =32 % 
AnalysisType ={'MS','MQS'};
DataType     ={'probeB','LossByJ','probeJ'};
StudyType    ={'_Load','NoLoad'};
ModelType    ={'ref','SC'};
LayerNumber  ={'4','3'};
LoadNumBWGraph   =length(AnalysisType)*(length(DataType)-1)*(length(StudyType)-1)*length(ModelType)*length(LayerNumber);
NumTotalGraph    =LoadNumBWGraph/length(ModelType)/length(AnalysisType);  % Load, probeB, LossyByJ, LayerNumber
% figure Num =Total Graph/(Model-with break yaxis) = 6
%+ NoLoad Graph - 
NoLoadNumBWGraph   =length(AnalysisType)*(length(DataType)-1)*(length(StudyType)-1)*(length(ModelType)-1)*length(LayerNumber);
addNoloadBW        =NoLoadNumBWGraph/length(AnalysisType);  % Noload, ProbeB, LossByJ, LayerNumber,
% Add Current Density
NoLoadNumJGraph   =(length(AnalysisType)-1)*(length(DataType)-2)*(length(StudyType)-1)*(length(ModelType))*length(LayerNumber);
addNoloadJ        =NoLoadNumJGraph/length(ModelType);  % Noload, ProbeJ, LayerNumber,
%% 



% D:\KangDH\Emlab_emach\mlxperPJT\JEET\devSettingProbeB.m
probeBFilePath=findCSVFiles(pwd);
PJTName     ='MQS';
BoolPJTName =contains(probeBFilePath,PJTName,'IgnoreCase',true)
BoolRef     =~contains(probeBFilePath,'ref','IgnoreCase',true)
BoolLoad    =contains(probeBFilePath,'_Load','IgnoreCase',true)
BoolProbeB  =contains(probeBFilePath,'ProbeB','IgnoreCase',true)
ProbeCSVPath=probeBFilePath(BoolPJTName&BoolLoad&BoolProbeB&BoolRef);
for CSVIndex=1:length(ProbeCSVPath)
    opts=delimitedTextImportOptions('NumVariables',1000);
    if exist(ProbeCSVPath{CSVIndex},"file")
    probeTableCell{CSVIndex,1}=readtable(ProbeCSVPath{CSVIndex},opts);
    probeTableCell{CSVIndex,2}=ProbeCSVPath{CSVIndex};
    end
end
%  Get parsing Data
MQSRefLoadProbeBTablesCellCaseRowDataCol = parseJMAGResultTable(probeTableCell{CSVIndex,1});
MQSRefLoadProbeBTablesCellCaseRowDataCol.Properties.Description=probeTableCell{CSVIndex,2};

MQSSCLoadProbeBTablesCellCaseRowDataCol = parseJMAGResultTable(probeTableCell{CSVIndex,1});
MQSSCLoadProbeBTablesCellCaseRowDataCol.Properties.Description=probeTableCell{CSVIndex,2};

save("MQSRefLoadProbeBTablesCellCaseRowDataCol.mat","MQSRefLoadProbeBTablesCellCaseRowDataCol")
save("MQSSCLoadProbeBTablesCellCaseRowDataCol.mat","MQSSCLoadProbeBTablesCellCaseRowDataCol")

TargetTable=MQSSCLoadProbeBTablesCellCaseRowDataCol;


LayerIndex=2;
for ModelIndex=1:2
    if ModelIndex==1  %% ref
        TargetTable=MQSRefLoadProbeBTablesCellCaseRowDataCol;
        BoolAbsVar        =contains(TargetTable.Properties.VariableNames,'Absolute');
        BoolRVar          =contains(TargetTable.Properties.VariableNames,'(R)');
        % BooltanVar        =contains(TargetTable.Properties.VariableNames,'(θ)');
        BoolZVar          =contains(TargetTable.Properties.VariableNames,'(Z)');
        ConductorIndex    =contains(TargetTable.Properties.VariableNames,num2str(LayerIndex));
        TargetTable=TargetTable(:,~BoolAbsVar&~BoolRVar&~BoolZVar&ConductorIndex);  % theta
        % TargetTable=TargetTable(:,BoolAbsVar&~BoolRVar&~BoolZVar&ConductorIndex);   % ABs
        % TargetTable=TargetTable(:,~BoolAbsVar&BoolRVar&~BoolZVar&ConductorIndex);   % R
    else
        TargetTable =MQSSCLoadProbeBTablesCellCaseRowDataCol;
        BoolAbsVar        =contains(TargetTable.Properties.VariableNames,'Absolute');
        BoolRVar          =contains(TargetTable.Properties.VariableNames,'(R)');
        % BooltanVar        =contains(TargetTable.Properties.VariableNames,'\Theta');
        BoolZVar          =contains(TargetTable.Properties.VariableNames,'(Z)');
        ConductorIndex    =contains(TargetTable.Properties.VariableNames,num2str(LayerIndex));
        TargetTable=TargetTable(:,~BoolAbsVar&~BoolRVar&~BoolZVar&ConductorIndex);  % theta
        % TargetTable=TargetTable(:,BoolAbsVar&~BoolRVar&~BoolZVar&ConductorIndex);   % ABs
        % TargetTable=TargetTable(:,~BoolAbsVar&BoolRVar&~BoolZVar&ConductorIndex);   % R
    end
% for caseIndex=1:height(TargetTable)
    % for DataIndex=1:width(TargetTable)
    for DataIndex=1:width(TargetTable)
        figure(caseIndex)
        tempTargetTable=TargetTable{caseIndex,DataIndex}{:};
        tempTargetTable=tempTargetTable([end-119:end],:);
        grphLineObj=plotTransientTable(tempTargetTable);
        ax=convertFigXAxisToElecDeg();
        % grphLineObj{1}.Marker='*'l
        ax.YLim=[-0.4 0.4];
        hold on
    end
% end

end
%% Single Value




%%
% 
% Total-DC Loss
% 
% 
%% SC 


%% Hybrid

%% Map단위로?