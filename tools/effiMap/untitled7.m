JMAGParentPath='F:\KDH\KDH';
parentPath='F:\KDH\Thesis\JEET'
[motFileList,~]=getResultMotMatList(parentPath);

MCAD=callMCAD;
mcad.LoadFromFile(motFileList{1})
filteredTable           =getMCADLabDataFromMotFile(motFileList{1});
originLabLinkTable      = reNameLabTable2LabLink(filteredTable);
MCADLinkTable           = originLabLinkTable;

tempFitResult = plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable, 'bilinear')
tempFitResult = plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable,'fit');



%% 
plotSubPlotbyStructAndstrCell(plotFitResult, structbyType.(structName), typeStrt.(cellName));
plotFitResult(fitresult, DataSet,1)


% [fitresult, gof, DataSet] = createInterpDataSetofStrWithFieldName_bilinear(buildDataStr, varName)

% [fitresult, gof, DataSet] = createInterpDataSetofStrWithFieldName_interp2(buildDataStr, varName)

 plotFitResultwithValidation(fitresult, DataSet, 1)

 buildDataStr=MCADLinkTable;
varNames = buildDataStr.Properties.VariableNames;

InputTable=MCADLinkTable;
i=10;
subPlotList = varNames;
varNames = InputTable.Properties.VariableNames;
varUnits = InputTable.Properties.VariableUnits;

if ~isempty(varUnits)
    nonAmpereIndex = (~strcmp(varUnits, 'A') & ~strcmp(varUnits, 'Amps')) & (~strcmp(varUnits, 'EDeg'));
    subPlotList = varNames(nonAmpereIndex);
else
    subPlotList = varNames;
end

% 필터링
subPlotList = removeCellwithMatchingStr(subPlotList, 'Sleeve_Loss');
subPlotList = removeCellwithMatchingStr(subPlotList, 'Coefficient');

% 그룹별 분류
typeStrt.voltageCell = getCellwithMatchingStr(subPlotList, 'V');
if isempty(typeStrt.voltageCell); typeStrt = rmfield(typeStrt, "voltageCell"); end

IronLossCell = getCellwithMatchingStr(subPlotList, 'Iron');
FE = getCellwithMatchingStr(subPlotList, 'FE');
typeStrt.IronLossCell = [IronLossCell FE];
if isempty(typeStrt.IronLossCell); typeStrt = rmfield(typeStrt, "IronLossCell"); end

LossCell = getCellwithMatchingStr(subPlotList, 'Loss');
LossCell = removeCellwithMatchingStr(LossCell, 'Fe');
LossCell = removeCellwithMatchingStr(LossCell, 'AC_Copper_Loss_(C1)');
typeStrt.LossCell = removeCellwithMatchingStr(LossCell, 'Iron');
if isempty(typeStrt.LossCell); typeStrt = rmfield(typeStrt, "LossCell"); end

otherCell = removeCellwithMatchingStr(subPlotList, 'Loss');
typeStrt.otherCell = removeCellwithMatchingStr(otherCell, 'V');
if isempty(typeStrt.otherCell); typeStrt = rmfield(typeStrt, "otherCell"); end

varName = subPlotList{i};
[tempFitResult, ~, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, varName);

fitresult=tempFitResult
DataSet=InputTable
plotDatatype='fit'