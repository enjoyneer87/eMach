function [tables, names, units] = splitTableByUnits(tableIn)
% tableIn : 분리할 데이터가 저장된 테이블

% 모든 변수의 단위 추출
units = unique(tableIn.Properties.VariableUnits);

% 각 단위별로 테이블 생성
tables = cell(1, length(units));
names = cell(1, length(units));
for i = 1:length(units)
    unitIdx = strcmp(tableIn.Properties.VariableUnits, units{i});
    tables{i} = tableIn(:, unitIdx);
    names{i} = tableIn.Properties.VariableNames(unitIdx);
end
end