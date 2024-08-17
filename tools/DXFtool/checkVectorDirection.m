function direction = checkVectorDirection(x, y)
    % 원점에서 벡터의 시작점과 끝점의 거리를 계산
    origin = [0, 0];
    startPoint = origin;
    endPoint = [x, y];
    
    % 벡터의 시작점과 끝점 간의 거리를 계산
    distanceFromOriginToEnd = norm(endPoint - startPoint);
    
    % 방향 벡터가 원점을 기준으로 바깥을 향하는지 원점쪽으로 향하는지 확인
    if distanceFromOriginToEnd > 0
        direction = 'Outwards'; % 바깥쪽으로 향함
    else
        direction = 'Inwards'; % 원점 쪽으로 향함
    end
end
