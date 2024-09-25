function [closestPoints, elementIDs] = findClosestPointsToRectangleCorners(elementTable)
    % 입력:
    % elementTable - x, y 좌표 및 elementID를 포함한 테이블

    % 사각형의 꼭지점과 중앙 좌표 (예: [xmin ymin], [xmin ymax], [xmax ymax], [xmax ymin])
    xmin = min(elementTable.x);
    xmax = max(elementTable.x);
    ymin = min(elementTable.y);
    ymax = max(elementTable.y);
    
    % 꼭지점과 중앙에 해당하는 기준점
    referencePoints = [xmin, ymin;   % Bottom-left
                       xmin, ymax;   % Top-left
                       xmax, ymax;   % Top-right
                       xmax, ymin;   % Bottom-right
                       (xmin+xmax)/2, ymin;    % Mid-bottom
                       (xmin+xmax)/2, ymax;    % Mid-top
                       xmin, (ymin+ymax)/2;    % Mid-left
                       xmax, (ymin+ymax)/2];   % Mid-right
    
    % 거리 계산 및 가장 가까운 좌표 찾기
    numPoints = size(referencePoints, 1);
    closestPoints = zeros(numPoints, 2);
    elementIDs = zeros(numPoints, 1);

    for i = 1:numPoints
        distances = sqrt((elementTable.x - referencePoints(i, 1)).^2 + (elementTable.y - referencePoints(i, 2)).^2);
        [~, minIndex] = min(distances);
        closestPoints(i, :) = [elementTable.x(minIndex), elementTable.y(minIndex)];
        elementIDs(i) = elementTable.id(minIndex);  % 해당 좌표의 elementID 반환
    end
end