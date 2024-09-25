function filterLegendByStrings(legendStrings)
    % 현재 figure에서 모든 legend 항목 가져오기
    currentLegend = findobj(gcf, 'Type', 'Legend');
    if isempty(currentLegend)
        disp('No legend found.');
        return;
    end
    
    % 현재 legend 항목의 텍스트 가져오기
    legendItems = currentLegend.String;
    
    % 필터할 legend 문자열 목록
    filteredItems = {};
    
    % 입력된 문자열과 동일한 legend만 남기기
    for i = 1:length(legendItems)
        if any(strcmp(legendItems{i}, legendStrings))
            filteredItems{end+1} = legendItems{i};
        end
    end
    
    % 남은 항목만 legend에 다시 설정
    if ~isempty(filteredItems)
        legend(filteredItems);
    else
        legend off;  % 필터링된 항목이 없으면 legend 비활성화
    end
end