function [nodeCoords, DT]=getNodePos(NodeID,studyObj)
    % x, y: 이미 알고 있는 임의의 점들의 좌표 (벡터)
    % d: 해당 점들과 미지의 점 사이의 거리 (벡터)
    % 이 함수는 미지의 점의 좌표 x0, y0을 반환합니다.
    numNodes = length(NodeID);

    % 노드 좌표를 저장할 배열
    nodeCoords = zeros(numNodes, 2); % 2D 좌표를 추정하기 위해 2열 배열 사용

    % 이미 알고 있는 점들의 좌표
    x_known = [1, 4, 6];  % 예시 x좌표
    y_known = [1, 5, 3];  % 예시 y좌표
    
    % 미지의 점 좌표 계산
    for i = 1:numNodes
        Distance(1)=JmagMeasureDistanceFrom(x_known(1),y_known(1),0,'Node',NodeID(i),studyObj);
        Distance(2)=JmagMeasureDistanceFrom(x_known(2),y_known(2),0,'Node',NodeID(i),studyObj);
        Distance(3)=JmagMeasureDistanceFrom(x_known(3),y_known(3),0,'Node',NodeID(i),studyObj);
        [xi, yi] = triangulatePosition(x_known, y_known, Distance);
        nodeCoords(i, :) = [xi, yi]; % 노드i의 좌표 저장
    end

    % uniquetol을 사용하여 허용 오차 내에서 고유 값을 찾음
    tol = 1e-5;  % 허용 오차 설정
    [nodeCoords, ~] = uniquetol(nodeCoords, tol, 'ByRows', true);

    DT = delaunayTriangulation(nodeCoords);  % The point set is unique;

end