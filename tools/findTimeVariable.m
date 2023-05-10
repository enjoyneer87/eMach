function [PlotMeasured,timeVarNames, xTime] = findTimeVariable(PlotMeasured)
% time 변수 이름을 찾음
timeVarNames = PlotMeasured.Properties.VariableNames(contains(PlotMeasured.Properties.VariableNames, 'Time'));

% time 변수 이름이 1개인 경우 xTime을 설정
if length(timeVarNames) == 1
    xTime = PlotMeasured.(timeVarNames{1});
    PlotMeasured = removevars(PlotMeasured, timeVarNames);

elseif length(timeVarNames) == 0
return
else
warning('여러 개 또는 없는 time 변수를 찾았습니다.')
xTime = [];
end

% time 변수 제거

end