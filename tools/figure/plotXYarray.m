function dataTable=plotXYarray(List_xvalue,List_valueforGraph,FigureData)
   if nargin>2
        if contains(FigureData.PlotType,'Comparison','IgnoreCase',true)  
        LineStyle='--';
        else
        LineStyle='-';
        end
    else
    LineStyle='-';
    end
  %% Plot
    plot(List_xvalue, List_valueforGraph,'LineWidth', 2,'LineStyle',LineStyle,'MarkerFaceColor','auto','DisplayName',FigureData.DisplayName)
    a = gca;
    a.XLabel.String = 'Electrical Angle[deg]';
    a.YLabel.String = FigureData.Unit;
    xlim([min(List_xvalue), max(List_xvalue)]);
    xticks(0:60:max(List_xvalue));
    % title(a,['@',num2str(ShaftSpeed)]);
 
%% 
    % 현재 figure와 axes의 핸들 가져오기
fig = gcf;
ax = gca;

% axes 내의 모든 plot 객체 가져오기
lines = findall(ax, 'Type', 'Line');

% 마커를 포함하는 plot의 개수 확인
numPlotsWithMarkers = sum(~cellfun('isempty', {lines.Marker}));

% 마커 종류 리스트 (필요에 따라 추가 가능)
markerTypes = {'o', 's', 'd', '^', 'v', '>', '<', 'p', 'h', '*', '+', 'x'};

% 현재 플롯이 몇 개인지 출력

% 각 plot에 마커 종류를 지정 (홀수는 마커를 비우고, 짝수는 채우기)
for i = 1:length(lines)
    if ~isempty(lines(i).Marker)
        % 마커 종류를 순환적으로 할당
        lines(i).Marker = markerTypes{mod(i-1, length(markerTypes)) + 1};
        
        % 홀수 번째 플롯은 마커를 비우고(흰색), 짝수 번째 플롯은 라인과 같은 색으로 채움
        if mod(i, 2) == 0
            lines(i).MarkerFaceColor = lines(i).Color;  % 채운 마커 (라인 색과 동일)
        else
            lines(i).MarkerFaceColor = 'w';  % 비워진 마커 (흰색으로 채움)
        end
    end
end
% 
% % 확인 메시지 출력
% disp('플롯의 마커 종류가 설정되었습니다.');
    %% Graph Setting
    % setGraphNameNoDigits = regexprep(setGraphName, '\d', ''); % Remove digits
    % titleText = [setGraphNameNoDigits, ' at ', num2str(ShaftSpeed), 'rpm'];
    % title(titleText);

    %% Legend Position

    % lgd = legend('Location', 'northoutside','Orientation', 'horizontal',NumColumns=3);
    % lgd.Box = 'off'; % 범례의 박스 표시를 없앰
    
    
    % 범례의 위치를 수동으로 조정
    % 예: 범례를 그래프 상단에 더 가깝게 위치시킴
    % lgdPos = lgd.Position;
    % lgd.Position = [lgdPos(1), lgdPos(2)+lgdPos(4), lgdPos(3), lgdPos(4)];

    formatter_sci
    
    %% Output 
    StepDivision=height(List_xvalue)-1;
    % freqE=rpm2freqE(ShaftSpeed,double(PoleNumber/2));
    % EndTime=1/freqE;
    % xTime=(0:(EndTime/StepDivision):EndTime)';
    % dataTable = table(xTime,List_xvalue, List_valueforGraph, 'VariableNames', {'Time','Angle', 'GraphValue'});
    dataTable = table(List_xvalue, List_valueforGraph, 'VariableNames', {'Angle', 'GraphValue'});

    YValue = max(List_valueforGraph);
    MeanValue = mean(List_valueforGraph);

    % ResultStructEmagCalc.dataTable = dataTable;
    % ResultStructEmagCalc.MaxValue = YValue;
    % ResultStructEmagCalc.meanValue = MeanValue;

end