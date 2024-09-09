app             =callJmag
PJTPath         =app.GetProjectFolderPath
Model           =app.GetCurrentModel
StudyIndex      =2
curStudyObj     =Model.GetStudy(StudyIndex-1)
curStudyObj.GetName

LossStudyResultTableObj=curStudyObj.GetResultTable;
% get DataStruct
jouleDataStruct   = getJMagResultDatas(LossStudyResultTableObj,'Joule');

ResultCSVPath     =exportJMAGAllCaseTables(app,'JEET');
% Part Data
FqfilterName={'Fq'};
parsedMSResultTableFromCSV=readJMAGWholeResultTables(FqfilterName);

tempJouleLossTable=parsedMSResultTableFromCSV{1}.("JouleLoss:W"){caseIndex(1)}
PartNameList      =tempJouleLossTable.Properties.VariableNames';
MQSSCLoadTable=parsedMSResultTableFromCSV{1}

targetName='Total';
% TotalJoule4Case=cell(length(speedList),1);
for TableIndex=2:2
    for caseIndex=1:height(MQSSCLoadTable)
    % speed2Plot=speedList(caseIndex);    
    table2Plot=MQSSCLoadTable{caseIndex,TableIndex}{1};
    varNames=table2Plot.Properties.VariableNames;
    % calc
    TotalJoule{caseIndex}=table2Plot(:,'Total');
    end
end

%% DTTable
ParameterListTable=getJMAGDesingTable(curStudyObj);

Bool45degIndex=contains(ParameterListTable.("Equation parameters: MCADPhaseAdvance"),'45')


speedList=ParameterListTable.("Equation parameters: speed")(Bool45degIndex)
 
Total45degJoule=TotalJoule(Bool45degIndex)

FreqList=convertCharCell2Numeric(plot2Table.Properties.RowNames)
RPMList=freq2rpm(elec2mech(FreqList,4))
for tableIndex=1:len(Total45degJoule)
plot2Table=Total45degJoule{tableIndex}
plot(RPMList,plot2Table.('Total')/1000,'DisplayName',speedList{tableIndex})
hold on
end