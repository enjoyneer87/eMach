function titleChildren = findAxesWithTitles(fig)
    % 주어진 figure의 children 가져오기
    children = get(fig, 'Children');    
    % title이 있는 figure handle children 찾기
    titleChildren = [];
    for i = 1:length(children)
        if isa(children(i), 'matlab.graphics.axis.Axes') % axes 객체인지 확인
            ax = children(i);
            if ~isempty(ax.Title) % 해당 axes에 title이 있는지 확인
                titleChildren = [titleChildren, ax]; % title이 있는 axes를 저장
            end
        end
    end
end