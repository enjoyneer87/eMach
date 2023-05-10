function plotTempRise(PlotMeasured, xTime)
% PlotMeasured: 플롯할 데이터가 있는 테이블
% xTime: x축 시간 데이터

for i = 1:width(PlotMeasured)
    varname = PlotMeasured.Properties.VariableNames{i};
    if all(PlotMeasured.(varname) > 0) && (contains(varname, 'degC') || contains(varname, 'Temp'))
        plot(xTime, PlotMeasured.(varname), 'DisplayName', strrep(varname, '_', ' '));
        hold on
        % displayName으로 넣을 이름 설정
        name = strrep(varname, '_', ' ');
        % x, y값 설정
        x = xTime(end-round(end/10));
        y = PlotMeasured.(varname)(end-round(end/10));
        % NaN이 아닌 가장 마지막 값으로 x, y 좌표 설정
        if isnan(x) || isnan(y)
            idx = find(~isnan(xTime), 1, 'last');
            x = xTime(idx);
            y = PlotMeasured.(varname)(idx);
        end
        % text 추가
%         adjusted_text(x,y,name,xTime,varData);
        text(x, y, name, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle')

    end
end
