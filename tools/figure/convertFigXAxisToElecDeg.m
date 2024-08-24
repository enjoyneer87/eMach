function ax=convertFigXAxisToElecDeg()
    ax = gca;                        % 현재 활성화된 Figure의 축을 가져옵니다.
    xData = get(ax, 'XTick');         % X축 데이터의 범위를 가져옵니다 (duration 형식일 것임).
    xTicks = 0:60:360;
    if isduration(xData)
        % X축의 duration 데이터를 0에서 360도로 매핑하기 위해 변환
        totalDuration = seconds(xData(end) - xData(1));
        timeTicks = seconds(xData(1)) + (xTicks / 360) * totalDuration;    
        % duration 형식으로 변환
        timeTicksDuration = seconds(timeTicks);
        % X축을 새로 설정
        set(ax, 'XTick', timeTicksDuration);
    else
        totalDuration =xData(end) - xData(1);
        timeTicks    = xData(1) + (xTicks / 360);  
        % X축을 0에서 360까지 60씩 증가하도록 설정합니다.
        set(ax, 'XTick', timeTicks);
    end

    strDegTickLabels=arrayfun(@num2str, xTicks, 'UniformOutput', false);
    set(ax, 'XTickLabel', strDegTickLabels);     % X축 라벨을 0에서 360으로 설정합니다.
    % X축 라벨을 "Degrees"로 설정합니다.
    xlabel(ax, 'Electrical Angle[deg]');
    grid on
    % 그래프가 데이터에 맞게 잘 보이도록 X축 범위를 조정합니다.
    % set(ax, 'XLim', [0 360]);
    % 필요에 따라 Y축 등 다른 설정도 추가할 수 있습니다.
end