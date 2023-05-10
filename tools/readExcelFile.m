function [tables, names, units] = readExcelFile(filepath)
% Excel 파일에서 모든 시트의 데이터를 읽어와서 각각의 table 형태로 반환하는 함수
% [tables, names, units] = readExcelFile(filepath)
% - filepath : 읽어올 파일의 경로
% - tables : 시트별로 읽어온 데이터를 저장한 table의 cell 배열
% - names : 열 이름을 저장한 cell 배열
% - units : 열의 단위를 저장한 cell 배열

% 파일 확장자 추출
[~, ~, ext] = fileparts(filepath);

if ~strcmp(ext,'.xlsx')
    error('Unsupported file extension. Only .xlsx files are supported.')
end

% 파일 내의 시트 이름 추출
[~, sheetNames] = xlsfinfo(filepath);

% 시트별로 데이터 읽어오기
numSheets = length(sheetNames);
tables = cell(1, numSheets);
for i = 1:numSheets
    % 파일 옵션 지정
    varopts = detectImportOptions(filepath, 'Sheet', sheetNames{i});
    varopts.VariableTypes = repmat("string", 1, length(varopts.VariableTypes));
%     varopts.DataRange = "A1:CN1";
    varopts.DataRange = [1, inf];
    strcell = readcell(filepath, varopts);
    variableNames=strcell(1,:);
    variableUnits=strcell(2,:);
    % 데이터 가져오기
    varopts.DataRange = [3, inf];
    varopts.VariableTypes = repmat({'double'}, 1, length(varopts.VariableTypes));
    tables{i}=readtable(filepath,varopts);
    variableNames=addIndexToDuplicateCells(variableNames);
    tables{i}.Properties.VariableNames=variableNames;
    tables{i}.Properties.VariableUnits=variableUnits;



    % cell 형태의 변수를 double 형태로 변환
    for j = 1:width(tables{i})
        if iscell(tables{i}.(j))
            % 해당 열이 모두 숫자로 변환이 가능한 경우에만 double 형태로 변환
            if all(cellfun(@isnumeric, tables{i}.(j)))
                tables{i}.(j) = cellfun(@str2double, tables{i}.(j));
            end
        end
    end
end


end