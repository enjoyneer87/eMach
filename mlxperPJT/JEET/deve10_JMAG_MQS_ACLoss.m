% Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\deve10_JMAG_MS_ACLoss.m
% dev10MQSplotAC
e10MQS_WireTemplate_38100 % 실행해서 JMAG파일 만들기
%%
CoilPattern=4;
Modelcase  =2;
ModeltableList=cell(CoilPattern*Modelcase,2);
JPJTList=findJPJTFiles(fileparts(app.GetProjectFolderPath));
BoolWireTemp=JPJTList(contains(JPJTList,'Peri','IgnoreCase',true))';
BoolPeriTemp=JPJTList(contains(JPJTList,'Pattern','IgnoreCase',true))';
MQSList=[BoolWireTemp;BoolPeriTemp];
app=callJmag;
for PJTIndex=7:len(MQSList)
    app.Load(MQSList{PJTIndex})
    app.CheckForNewResults()
    exportJMAGAllCaseTables(app,'JEET');
end
%% Find CSV
% PJTName='MQS';
ResultFilePath=findCSVFiles(pwd);
ResultFilePath=ResultFilePath(contains(ResultFilePath,'Pattern',"IgnoreCase",true));
ResultFilePath=ResultFilePath(~contains(ResultFilePath,'Fq',"IgnoreCase",true));
ResultFilePath=ResultFilePath(~contains(ResultFilePath,'Map',"IgnoreCase",true));

resultTableCell=cell(length(ResultFilePath),1);
AppNumStudies=length(ResultFilePath);
for AppStudyIndex=1:AppNumStudies
    % opts=detectImportOptions(ResultFilePath{7})
    opts=delimitedTextImportOptions('NumVariables',1500);
    if exist(ResultFilePath{AppStudyIndex},"file")
        resultTableCell{AppStudyIndex,1}=readtable(ResultFilePath{AppStudyIndex},opts);
        resultTableCell{AppStudyIndex,2}=ResultFilePath{AppStudyIndex};
    end
end


%% 
CSVTableList=cell(len(resultTableCell),2);
for LoadStudyIndex=1:len(resultTableCell)
    targetTable = parseJMAGResultTable(resultTableCell{LoadStudyIndex,1});
    targetTable.Properties.Description=resultTableCell{LoadStudyIndex,2};
    CSVTableList{LoadStudyIndex,1}=targetTable;
end
save('Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\From38002\CSVTableList.mat',"CSVTableList")
targetName='Total';
% speedList=1000:2000:15000;
for ModelIndex=1:len(CSVTableList)
    TargetTable=CSVTableList{ModelIndex,1};
    for TableIndex=2:2  % Joule Loss
        speedList=cell(1,height(TargetTable));
        JouleAvgTablCell4Case=cell(len(speedList),2);
        for caseIndex=1:height(TargetTable)
            % speed2Plot=speedList(caseIndex);
            table2Plot=TargetTable{caseIndex,TableIndex}{1};
            speedList{1,caseIndex}=['case',num2str(caseIndex),'speed',num2str(freqE2rpm(1/seconds(table2Plot.Time(121)),4))];
            varNames=table2Plot.Properties.VariableNames;
            if any(contains(varNames,targetName,"IgnoreCase",true))
                % calc
                table2plotPerVarNames=table2Plot(:,varNames);
                JouleAvgTablCell4Case{caseIndex,1}=varfun(@mean ,table2plotPerVarNames(end-120:end,:),"OutputFormat","table");
                JouleAvgTablCell4Case{caseIndex,2}=JouleAvgTablCell4Case{caseIndex,1}(:,end).Variables;
            end
        end
            JouleAvgTablCell4CaseTable=cell2table(JouleAvgTablCell4Case);
            JouleAvgTablCell4CaseTable.Properties.VariableNames={'JouleTable','JouleAvg'};
            JouleAvgTablCell4CaseTable.Properties.RowNames=speedList;
    end
    CSVTableList{ModelIndex,2}=JouleAvgTablCell4CaseTable;
end

%% SCL
targetName='Total';
speedList=1000:2000:15000;
JouleAvgTablCell4Case=cell(length(speedList),2);
for ModelIndex=1:2
TargetTable=ModeltableList{ModelIndex,1};
for TableIndex=2:2  % Joule Loss
for caseIndex=1:height(TargetTable)
speed2Plot=speedList(caseIndex);
table2Plot=TargetTable{caseIndex,TableIndex}{1};
varNames=table2Plot.Properties.VariableNames;
if any(contains(varNames,targetName,"IgnoreCase",true))
% calc
table2plotPerVarNames=table2Plot(:,varNames);
JouleAvgTablCell4Case{caseIndex,1}=varfun(@mean ,table2plotPerVarNames(end-120:end,:),"OutputFormat","table");
JouleAvgTablCell4Case{caseIndex,2}=JouleAvgTablCell4Case{caseIndex,1}(:,end).Variables;
end
end
JouleAvgTablCell4CaseTable=cell2table(JouleAvgTablCell4Case)
JouleAvgTablCell4CaseTable.Properties.VariableNames={'JouleTable','JouleAvg'}
end
ModeltableList{ModelIndex,2}=JouleAvgTablCell4CaseTable;
end
ModeltableList
Modeltable=cell2table(ModeltableList)
ModelTable=cell2table(ModeltableList)
ModelTable.Properties.VariableNames={'LoadTable','JouleTable'}
ModelTable.Properties.RowNames={'REF','SCL'}
ResultFilePath
[~,CSVDir,~]=filepart(ResultFilePath{1})
[~,CSVDir,~]=fileparts(ResultFilePath{1})
[CSVDir,DirName,~]=fileparts(ResultFilePath{1})
[CSVDir,~,~]=fileparts(ResultFilePath{1})
save(fullfile(CSVDir,'MQSTableFrom38100.mat'),"ModelTable")


%% Load MQS List



%%  Get All Data
BoolLoad  =contains(resultTableCell(:,2),'_Load','IgnoreCase',true);
BoolRef   =contains(resultTableCell(:,2),'ref','IgnoreCase',true);
BoolProbe =contains(resultTableCell(:,2),'Probe','IgnoreCase',true);
BoolBy =contains(resultTableCell(:,2),'By','IgnoreCase',true);

AppStudyIndex =(BoolRef&BoolLoad&~BoolProbe&~BoolBy);
LoadStudyIndex=find(AppStudyIndex)
MQSRefLoadTable = parseJMAGResultTable(resultTableCell{LoadStudyIndex,1});
MQSRefLoadTable.Properties.Description=resultTableCell{LoadStudyIndex,2};

AppStudyIndex =(~BoolRef&BoolLoad&~BoolProbe&~BoolBy);
find(AppStudyIndex)

MQSSCLoadTable = parseJMAGResultTable(resultTableCell{AppStudyIndex,1});
MQSSCLoadTable.Properties.Description=resultTableCell{AppStudyIndex,2};
TargetTable=MQSSCLoadTable;

% TablesCellCaseRowDataCol - 전체 결과 Waveform
%% ref
MCAD=callMCAD
PhaseNumber=3;
RefPhaseActResistance=0.007;
refDCLoss=(650.5/sqrt(2)).^2*PhaseNumber*RefPhaseActResistance
% CurrentMotFilePath=getCurrentMotFilePath(MCAD)
% [SCMachine,filteredLabTable4Scaling]=getMCADData4ScalingFromMotFile(CurrentMotFilePath)

SCPhaseActResistance=RefPhaseActResistance/4
% SCPhaseActResistance=SCMachine.MotorCADGeo.ResistanceActivePart
SCDCLoss=(2*650.5/sqrt(2)).^2*PhaseNumber*SCPhaseActResistance;

%% Speed ListP
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
% LossLine(1)=plot(speedList,refACLoss,'*-','DisplayName','ref AC Loss');
LossLine(1)=plot(speedList,[JouleAvgTablCell4Case{:,2}]/1000,'*-','DisplayName','ref Winding Loss');

xlabel('Rotor Speed[RPM]')
% ylabel('Total AC Loss[kW]')
ylabel('Total Winding Loss[kW]')

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
% LossLine(2)=plot(speedList,SCACLoss,'^-','DisplayName','SC AC Loss')
LossLine(2)=plot(speedList,[SCJouleAvgTablCell4Case{:,2}]/1000,'^-','DisplayName','SC Winding Loss')

xlabel('Rotor Speed[RPM]')
ylabel('Total Winding Loss[kW]')

% ylabel('Total AC Loss[kW]')
LossLine(2).Color='K'

% yyaxis right
% Ratio=plot(speedList,SCACLoss./refACLoss,'--');
% ylabel('Ratio SC/Ref')
% Ratio.Color='r';


%% Wave form B / LOSSDense/Current Density
devSettingProbeB
devSettingProbeJ
devSettingProbeJouleLoss
%% -Get Data - B
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

load("MQSSCLoadProbeBTablesCellCaseRowDataCol.mat")
load("MQSRefLoadProbeBTablesCellCaseRowDataCol.mat")

TargetTable=MQSSCLoadProbeBTablesCellCaseRowDataCol;

caseIndex=1
%%--Plot
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
        tempTargetTable=tempTargetTable([end-120:end],:);
        grphLineObj=plotTransientTable(tempTargetTable);
        ax=convertFigXAxisToElecDeg();
        % grphLineObj{1}.Marker='*'l
        ax.YLim=[-0.4 0.4];
        hold on
    end
% end
end

%% Plot J
probeBFilePath=findCSVFiles(pwd);
PJTName     ='MQS';
BoolPJTName =contains(probeBFilePath,PJTName,'IgnoreCase',true)
BoolRef     =~contains(probeBFilePath,'ref','IgnoreCase',true)
BoolLoad    =contains(probeBFilePath,'_Load','IgnoreCase',true)
BoolProbeB  =~contains(probeBFilePath,'ProbeB','IgnoreCase',true)
BoolProbeJ  =contains(probeBFilePath,'Probej','IgnoreCase',true)

ProbeCSVPath=probeBFilePath(BoolPJTName&BoolLoad&BoolProbeB&BoolProbeJ&BoolRef);
for CSVIndex=1:length(ProbeCSVPath)
    opts=delimitedTextImportOptions('NumVariables',1000);
    if exist(ProbeCSVPath{CSVIndex},"file")
    probeTableCell{CSVIndex,1}=readtable(ProbeCSVPath{CSVIndex},opts);
    probeTableCell{CSVIndex,2}=ProbeCSVPath{CSVIndex};
    end
end
%  Get parsing Data
MQSRefLoadProbeJ_TablesCellCaseRowDataCol = parseJMAGResultTable(probeTableCell{CSVIndex,1});
MQSRefLoadProbeJ_TablesCellCaseRowDataCol.Properties.Description=probeTableCell{CSVIndex,2};
MQSSCLoadProbeJ_TablesCellCaseRowDataCol = parseJMAGResultTable(probeTableCell{CSVIndex,1});
MQSSCLoadProbeJ_TablesCellCaseRowDataCol.Properties.Description=probeTableCell{CSVIndex,2};

caseIndex=1
%%--Plot
for LayerIndex=2:3
    for ModelIndex=1:1
        if ModelIndex==1  %% ref
            TargetTable=MQSRefLoadProbeJ_TablesCellCaseRowDataCol;
            BoolZVar          =contains(TargetTable.Properties.VariableNames,'(Z)');
            ConductorIndex    =contains(TargetTable.Properties.VariableNames,num2str(LayerIndex));
            TargetTable=TargetTable(:,BoolZVar&ConductorIndex);   % ABs
        else
            TargetTable =MQSSCLoadProbeJ_TablesCellCaseRowDataCol;
            BoolZVar          =contains(TargetTable.Properties.VariableNames,'(Z)');
            ConductorIndex    =contains(TargetTable.Properties.VariableNames,num2str(LayerIndex));
            TargetTable=TargetTable(:,BoolZVar&ConductorIndex);  % theta
        end
    % for caseIndex=1:height(TargetTable)
        % for DataIndex=1:width(TargetTable)
        for DataIndex=1:width(TargetTable)
            figure(LayerIndex)
            tempTargetTable=TargetTable{caseIndex,DataIndex}{:};
            tempTargetTable=tempTargetTable([end-120:end],:);
            grphLineObj=plotTransientTable(tempTargetTable);
            ax=convertFigXAxisToElecDeg();
            % grphLineObj{1}.Marker='*'l
            % ax.YLim=[-0.4 0.4];
            hold on
        end
    % end
    end
end


%% Result Table Get Joule Loss 

%% Per Layer (No Left & Right)
% init ResultTable N grphObj Cell
filterName={'_Periodic','MQS'}
tempCellResultTableFromCSV=readJMAGWholeResultTables(filterName)';
MQSResultTableFromCSV=cell(length(tempCellResultTableFromCSV),3);
MQSResultTableFromCSV=cell2table(MQSResultTableFromCSV);
MQSResultTableFromCSV.Properties.VariableNames={'ResultTable','CSVPath','Name4Mat'};
MQSResultTableFromCSV{:,1}=tempCellResultTableFromCSV;

grphLineObj=cell(height(MQSResultTableFromCSV),1);

% parsing 4plot  Loop Defin
% speedList=[1000:2000:13000];
caseIndex=1:length(speedList);
LayerIndexList=[4,3,2,1];
SlotIndexList =[6 12];
PJTNameList   ={'MQS'}; % !!! add Hybrid MS
ModelNameList ={'ref','SC'}
% Count LoopNumber
NumsingleGraph=length(caseIndex)*len(LayerIndexList)*len(SlotIndexList)*len(PJTNameList)*len(ModelNameList);
NumFigure     = NumsingleGraph/len(speedList)/len(ModelNameList);

startFromZero=0;
lineStyleList={'--','None','None'}
linecolor ={'k','b'};  %'k'= MQS, 'b'=MS
markerList={'+' , 'o' , '*' , '.' , 'x' , 'square' , 'diamond' , 'v' , '^' , '>' , '<' , 'pentagram' , 'hexagram' , ',' , '_' };

%%  Init Variable
% YLimitRange=[-0.4 0.4];
YLabelName ='Joule Loss[W]';
YLimitRange=[-1000 8000];
DCLossPerLayer=DCLossWaveformByIwaveVph/8


%% dev pre MQS Joule Loss
tempJouleLossTable=tempCellResultTableFromCSV{1}.("JouleLoss:W"){caseIndex(1)}
PartNameList      =tempJouleLossTable.Properties.VariableNames';
WirePartName='Wire'
SlotWirePartName  =PartNameList(contains(PartNameList,WirePartName,'IgnoreCase',true));
if ~isempty(SlotWirePartName)
    disp(['도체이름은 "',WirePartName,'"'])
end
grhLinIndex=0;
LineStyle='--'


DCGraph  =cell(1,8);
meanLine =cell(1,8);
linecolor=[217, 83, 25]/256
% for speedIndex=1:3:length(speedList)
for speedIndex=1:6
    for LayerNumIndex=1:len(LayerIndexList)
        for SlotIndex=1:len(SlotIndexList)
            for PJTNameIndex=1:len(PJTNameList)
                % for ModelNameIndex=1:len(ModelNameList)
                for ModelNameIndex=1:1
                    tempResultTable=MQSResultTableFromCSV.ResultTable{ModelNameIndex};
                    PJTModelNStudyName4Bool=tempResultTable.Properties.Description;
                    %% Bool Table
                    BoolPJTName   =contains(PJTModelNStudyName4Bool,PJTNameList{PJTNameIndex},'IgnoreCase',true);
                    BoolModelName =contains(PJTModelNStudyName4Bool,ModelNameList{ModelNameIndex},'IgnoreCase',true);
                    if BoolPJTName&&BoolModelName
                        tempResultTable=MQSResultTableFromCSV.ResultTable{ModelNameIndex};
                    else
                        continue
                    end
                    curJouleLossTable=tempResultTable.("JouleLoss:W"){speedIndex};
                    speed=freqE2rpm(1/seconds(curJouleLossTable.Time(121)),pole/2);
                    % if ~checkRPM
                    %    disp('rpm이 다릅니다')
                    %    continue
                    % end
                    curPartNameList   =curJouleLossTable.Properties.VariableNames;
                    % Bool Table VarNmae
                    BoolSlot      =contains(curPartNameList,['Slot',num2str(SlotIndexList(SlotIndex))],"IgnoreCase",true);
                    BoolWireNumber=contains(curPartNameList,['Wire',num2str(LayerIndexList(LayerNumIndex))],"IgnoreCase",true);
                    %% Plot 
                    % for figureIndex=1:4
                    % figure(figureIndex) 
                    % %% eachLayer
                    % tempTargetTable=curJouleLossTable(end-120:end,BoolWireNumber&BoolSlot);           
                    % % OnlyAcLossArray=tempTargetTable.Variables-DCLossPerLayer;
                    % % grphLineObj(grhLinIndex+1)=plotTransientTable(OnlyAcLossArray);
                    % % grphLineObj(grhLinIndex+1)=plotTransientTable(tempTargetTable.Variables);
                    % % curName=grphLineObj{grhLinIndex+1}.DisplayName;
                    % grphLineObj{grhLinIndex+1}.MarkerIndices=[1:3:len( grphLineObj{grhLinIndex+1}.MarkerIndices)];
                    % curName=['Conductor ' num2str(LayerNumIndex)]
                    % NewName=[ModelNameList{ModelNameIndex},' ',curName,'@',num2str(speed)];
                    % grphLineObj{grhLinIndex+1}.DisplayName=NewName;
                    % hold on
                    % % Color
                    % if contains(PJTModelNStudyName4Bool,'MS')
                    % linecolor=[0 114 189]/256+(PJTNameIndex-1)*60/256;
                    % BoolMQS=0;
                    % grphLineObj{grhLinIndex+1}.MarkerFaceColor=linecolor;
                    % else
                    %     linecolor=[217, 83, 25]/256+(PJTNameIndex-1)/2*60/256;
                    %     BoolMQS=1;
                    % end
                    % grphLineObj{grhLinIndex+1}.Color=linecolor;
                    % if contains(PJTModelNStudyName4Bool,'ref')
                    % grphLineObj{grhLinIndex+1}.Marker         ='o';
                    % else
                    % grphLineObj{grhLinIndex+1}.Marker     ='^';
                    % end
                    % grphLineObj{grhLinIndex+1}.LineWidth=2;
                    % grphLineObj{grhLinIndex+1}.LineStyle=LineStyle;
                    %  ax=convertFigXAxisToElecDeg(0);
                    %  % grphLineObj{1}.Marker='*'l
                    %  ax.YLim=YLimitRange;
                    %  ylabel(ax, YLabelName);
                    %  formatterFigure4Paper('Double','2x2');
                    %  grhLinIndex=grhLinIndex+1;      
                    % end
                    % %%
                end % 1st Model  - ref, sc 
            end     %PJT         - MQS
        end         %Slot        - 6 
    end             %LayerNumber%  - 4 3


    curJouleLossTable=tempResultTable.("JouleLoss:W"){speedIndex};
    speed=freqE2rpm(1/seconds(curJouleLossTable.Time(121)),pole/2);
                    for figureIndex=1:4
                    figure(figureIndex) 
                    AllSlotsTable          =curJouleLossTable(end-120:end,BoolSlot);
                    SumAllColumns          =sum(AllSlotsTable{:, :}, 2);
                    DCGraph{figureIndex} =plotTransientTable(SumAllColumns); % Plot 1
                    DCGraph{figureIndex}{1}.LineWidth=2;
                    DCGraph{figureIndex}{1}.LineStyle='-';
                    DCGraph{figureIndex}{1}.Marker         ='o';
                    DCGraph{figureIndex}{1}.Color=linecolor;    
                    DCGraph{figureIndex}{1}.DisplayName='DC+AC Slot6 MQS';
                    meanLine{figureIndex}=yline(mean(SumAllColumns));
                    meanLine{figureIndex}.DisplayName=['Mean ','DC+AC Slot6 MQS',num2str(speed)];
                    meanLine{figureIndex}.LineWidth=2;
                    meanLine{figureIndex}.LineStyle='-';
                    meanLine{figureIndex}.Color=linecolor;
                    hold on
                    textObj(figureIndex)=text(180,mean(SumAllColumns)*1.02,[num2str(mean(SumAllColumns),'%.2f'),'@',num2str(speed)]);
                    textObj(figureIndex).FontSize=12;
                    textObj(figureIndex).Color=linecolor;
                    formatterFigure4Paper('Double','2x2');
                    ax=convertFigXAxisToElecDeg(0);
                    end
end                 %Speed (Case)  -7



%%
% 
% Total-DC Loss
% 
% 
%% SC 


%% Hybrid

%% Map단위로?