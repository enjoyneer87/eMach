function swapZandXAxes()
    % 현재 figure의 x 축과 z 축 데이터를 가져옵니다.
    ax = gca;  % 현재 축 얻어오기
    xData = get(ax, 'XData');
    zData = get(ax, 'ZData');

    % x 축과 z 축 데이터를 바꿉니다.
    set(ax, 'XData', zData);
    set(ax, 'ZData', xData);

    % x 축과 z 축 라벨을 바꿉니다.
    xlabel('Z 축');
    zlabel('X 축');
end
