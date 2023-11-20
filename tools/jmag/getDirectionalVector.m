function directionVector = getDirectionalVector(startPoint, endPoint)
    % startPoint와 endPoint는 3차원 벡터로 표현된 시작점과 끝점입니다.
    startPoint=convertXYZData2Array(startPoint);
    endPoint=convertXYZData2Array(endPoint);
    % 방향 벡터 계산
    directionVector = endPoint - startPoint;
    
    % 방향 벡터를 단위 벡터로 정규화
    directionVector = directionVector / norm(directionVector);
end
