function plotTransientTable(table2Plot, StepData)
%% devTemp
% table2Plot=ResultTable
%%
    if isvarofTable(table2Plot,'Time') 
    % StepData.StartTime   =table2Plot{1,1};
    % StepData.EndTime     =table2Plot{end,1};
    StepData.StartTime   =table2Plot.Time(1);
    StepData.EndTime     =table2Plot.Time(end);
    StepData.StepDivision=height(table2Plot)-1;
    elseif nargin>1
    StepData=StepData;
    else
    StepData.StartTime   =table2Plot{1,1};
    StepData.EndTime     =table2Plot{end,1};
    end

   
    % StartTime   =StepData.StartTime;
    EndTime     =StepData.EndTime;
    StepDivision=StepData.StepDivision;
    xTime=(0:(EndTime/StepDivision):EndTime)';
    
    heightTable=height(table2Plot);
    % Single Period
    if heightTable>StepDivision
    table2Plot = table2Plot(heightTable-(StepDivision)+1:end, :);
    end


    % 각 변수에 대해 그래프를 그림
    for i = 1:width(table2Plot)
        varName = table2Plot.Properties.VariableNames{i}; % 변수 이름
        % varUnit = table2Plot.Properties.VariableUnits{1}; % 변수 단위
        if height(table2Plot)==height(xTime)-1 && ~contains(varName,'Angle','IgnoreCase',true) 
        plot(xTime(2:end),table2Plot.(varName), 'DisplayName', strrep(varName, '_', ' '));
        hold on;
        end
        % Y축 라벨 설정: 변수 이름과 단위를 포함
        % ylabel(['[', varUnit, ']']);
    end
    
    hold off; % 다음 그래프를 위해 hold 상태 해제
    formatter_sci; % Y축 포맷터 설정 함수 호출 (이 함수의 구현 내용은 제공되지 않았음)
    
    % 그래프 제목 및 축 이름 설정
    % title('Transient Data Plot');
    xlabel('Time [s]'); % X축 라벨은 시간으로 가정
end