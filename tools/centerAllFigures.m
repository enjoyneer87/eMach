function centerAllFigures()
    % 모든 떠 있는 figure를 얻어옵니다.
    openFigures = findall(0, 'type', 'figure');

    % 현재 사용 중인 MATLAB 버전에 맞는 디스플레이 크기를 얻어옵니다.
    screen_size = get(groot, 'ScreenSize');

    % 각각의 figure를 화면 중앙으로 이동합니다.
    for i = 1:numel(openFigures)
        figure_x = screen_size(3)/2 - openFigures(i).Position(3)/2;
        figure_y = screen_size(4)/2 - openFigures(i).Position(4)/2;
        set(openFigures(i), 'Position', [figure_x, figure_y, openFigures(i).Position(3), openFigures(i).Position(4)]);
    end
end
