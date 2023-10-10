function setAllFiguresView(az, el)
    % 현재 열린 모든 figure를 얻어옵니다.
    allFigures = findall(0, 'Type', 'figure');

    % 각 figure에 대해 view(az, el) 설정합니다.
    for i = 1:numel(allFigures)
        figure(allFigures(i));  % 현재 figure 설정
        view(az, el);  % 지정된 az와 el 값으로 설정
    end
end
