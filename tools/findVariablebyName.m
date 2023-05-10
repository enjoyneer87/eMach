function [dataTable,VarNames, Var] = findVariablebyName(dataTable,name)
VarNames = dataTable.Properties.VariableNames(contains(dataTable.Properties.VariableNames, name,'IgnoreCase', true)); % 'Torque' 변수 이름에 해당하는 열 추출

% 변수 이름이 1개인 경우
if length(VarNames) == 1
    Var = dataTable.(VarNames{1});
elseif length(VarNames) == 0
return
else
warning('여러 개 또는 없는 변수를 찾았습니다.')
Var = [];
end
end
