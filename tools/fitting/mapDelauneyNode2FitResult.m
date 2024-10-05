function [mapped_Btvalues,BoolconvexhulLine,in_polygonMask]=mapDelauneyNode2FitResult(fitresult,DT,yesPlot)
    nodes_x = DT.Points(:,1);  % 들로네 삼각분할의 노드 x 좌표
    nodes_y = DT.Points(:,2);  % 들로네 삼각분할의 노드 y 좌표
    
    mapped_Btvalues = feval(fitresult, nodes_x, nodes_y);
    
    BoolconvexhulLine = convhull(nodes_x, nodes_y);
    
    % 최외각 경계 내부에 해당하는 지점만을 추출하는 마스크 생성
    in_polygonMask = inpolygon(nodes_x, nodes_y, nodes_x(BoolconvexhulLine), nodes_y(BoolconvexhulLine));
    % 마스크를 적용하여 해당 영역만 남김
    mapped_Btvalues(~in_polygonMask) = NaN;  % 폴리곤 외부의 값은 NaN으로 설정

    %% plot
    if nargin>2
    plot3(nodes_x(BoolconvexhulLine), nodes_y(BoolconvexhulLine), mapped_Btvalues(BoolconvexhulLine), 'r-', 'LineWidth', 2);  % 경계선을 빨간색으로 표시
    hold on
    plot(nodes_x(BoolconvexhulLine), nodes_y(BoolconvexhulLine));
    centerAllFigures;
    end
end