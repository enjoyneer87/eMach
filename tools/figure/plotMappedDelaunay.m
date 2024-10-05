function trSurf=plotMappedDelaunay(DT,fitresult)
    %% refer fitting 
    % fitElementCenterData
    % mapDelauneyNode2FitResult
    nodes_x=DT.Points(:,1);
    nodes_y=DT.Points(:,2);
    triConn=DT.ConnectivityList;
    %% Mapping
    [mappedValues,~,in_polygon]=mapDelauneyNode2FitResult(fitresult,DT);
    %% triSurf
    trSurf=trisurf(triConn,nodes_x, nodes_y, mappedValues, ...
            'EdgeColor', 'none','FaceAlpha',0.5, 'FaceColor', 'interp');  % 'ConnectivityList' 사용하여 삼각형 구성
    xlabel('X Position [mm]');
    ylabel('Y Position (mm]');
    colorbar;  % 색상 막대 추가
    view(3);   % 3D 보기 활성화
    grid on;
    hold on;  % 추가 플롯을 위해 hold on
    %% Mesh Line 3d
    for i = 1:size(triConn, 1)
    x_edge = [nodes_x(triConn(i, 1)), nodes_x(triConn(i, 2)), nodes_x(triConn(i, 3)), nodes_x(triConn(i, 1))];
    y_edge = [nodes_y(triConn(i, 1)), nodes_y(triConn(i, 2)), nodes_y(triConn(i, 3)), nodes_y(triConn(i, 1))];
    z_edge = [mappedValues(triConn(i, 1)), mappedValues(triConn(i, 2)), mappedValues(triConn(i, 3)), mappedValues(triConn(i, 1))];
    plot3(x_edge, y_edge, z_edge, '-','color',greyColor, 'LineWidth', 1);  % 검정색 경계선
    end
    %% in_polygon이 true인 Mapped 점들만 시각화
    scatter3(nodes_x(in_polygon), nodes_y(in_polygon), mappedValues(in_polygon), ...
         'k','Marker','.');  % 빨간색으로 표시
end