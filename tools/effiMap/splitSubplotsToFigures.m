function splitSubplotsToFigures()
    % 현재 figure를 얻어옵니다.
    currentFigure = gcf;
    
    % 현재 figure가 서브플롯을 가지고 있는지 확인합니다.
    if ~isfield(currentFigure, 'Children') || isempty(currentFigure.Children)
        disp('The current figure does not have subplots to split.');
        return;
    end

    % 현재 figure의 서브플롯 개수를 얻어옵니다.
    numSubplots = numel(currentFigure.Children);

    % 각각의 서브플롯을 별도의 figure로 옮깁니다.
    for i = 1:numSubplots
        % 새로운 figure를 생성하고 서브플롯의 내용을 복사합니다.
        newFigure = figure;
        ax = gca;
        copyobj(currentFigure.Children(i).Children, ax);
        
        % 서브플롯 제목을 figure의 제목으로 설정합니다.
        subplotTitle = currentFigure.Children(i).Title;
        if ~isempty(subplotTitle)
            newFigure.Name = subplotTitle.String;
        end
    end
    
    % 현재 figure의 서브플롯을 삭제합니다.
    clf(currentFigure);
end
