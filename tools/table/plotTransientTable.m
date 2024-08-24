function grphLineObj=plotTransientTable(table2Plot, var2Plot,StepData)
%% devTemp
% table2Plot=ResultTable
% table2Plot=DataSetTable
% table2Plot=TablesCellCaseRowDataCol{1,2}{1}
%%
    if istimetable(table2Plot)
        xTime = timerange(table2Plot.Time(1),table2Plot.Time(end));
        table2Plot = table2Plot(xTime, :);
        varName = table2Plot.Properties.VariableNames; % 변수 이름       
        % 각 변수에 대해 그래프를 그림
        if nargin==2
            var2PlotList=varName(contains(varName,var2Plot,'IgnoreCase',true));
        else
            var2PlotList=varName;
        end
            for i = 1:width(var2PlotList)
                if ~isempty(table2Plot.(var2PlotList{i}))
                % varUnit = table2Plot.Properties.VariableUnits{i}; % 변수 단위
                grphLineObj{i}=plot(table2Plot.Time,table2Plot.(var2PlotList{i}), 'DisplayName', [strrep(var2PlotList{i}, '_', ' ')]);
                hold on;
                else
                close
                end
                % Y축 라벨 설정: 변수 이름과 단위를 포함
                % ylabel(['[', varUnit, ']']);
            end     
    elseif istable(table2Plot)
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
            varName = table2Plot.Properties.VariableNames; % 변수 이름
            % varUnit = table2Plot.Properties.VariableUnits{1}; % 변수 단위
            if height(table2Plot)==height(xTime)-1 && ~contains(varName,'Angle','IgnoreCase',true) 
            grphLineObj{i}=plot(xTime(2:end),table2Plot.(varName), 'DisplayName', strrep(varName, '_', ' '));
            hold on;
            end
            % Y축 라벨 설정: 변수 이름과 단위를 포함
            % ylabel(['[', varUnit, ']']);
        end

    end


    
    % hold off; % 다음 그래프를 위해 hold 상태 해제
    formatter_sci; % Y축 포맷터 설정 함수 호출 (이 함수의 구현 내용은 제공되지 않았음)
    legend
    % 그래프 제목 및 축 이름 설정
    xlabel('Time [s]'); % X축 라벨은 시간으로 가정
end