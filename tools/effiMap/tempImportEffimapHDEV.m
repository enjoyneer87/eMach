

filepath="Z:\01_Codes_Projects\Testdata_post\수소동력 65도 부분부하 효율 평균정리_V5.csv"
% filepath='Z:\01_Codes_Projects\Testdata_post\Total_Effy_skew_rework_HDEV.csv'
[dataTable, NameCell]=readDataFile(filepath,40)
NumVariables=40

% 파일 옵션 지정
fileOpts = delimitedTextImportOptions("NumVariables", NumVariables, "Encoding", "UTF-8");
fileOpts.DataLines = [1, inf];
fileOpts.Delimiter = ",";
fileOpts.VariableTypes = repmat({'char'}, 1, NumVariables);
fileOpts.ExtraColumnsRule = "ignore";
fileOpts.EmptyLineRule = "read";

% 데이터 가져오기
dataInfoTable = readtable(filepath, fileOpts);

% 데이터 전처리
nameCell = table2cell(dataInfoTable(1,:));
unitCell = table2cell(dataInfoTable(2,:));

dataOpts = delimitedTextImportOptions("NumVariables", NumVariables, "Encoding", "UTF-8");
dataOpts.DataLines = [3, inf];
dataOpts.Delimiter = ",";
dataOpts.VariableTypes = repmat({'double'}, 1, NumVariables);
dataOpts.ExtraColumnsRule = "ignore";
dataOpts.EmptyLineRule = "read";

dataTable = readtable(filepath, dataOpts);


dataArr = table2array(dataTable);

nanCols = any(isnan(dataArr), 1);

clear dataArr dataOpts fileOpts 
dataTable = dataTable(:, ~nanCols);
nameCell = nameCell(:, ~nanCols);
unitCell = unitCell(:, ~nanCols);
dataTable.Properties.VariableNames = nameCell;
