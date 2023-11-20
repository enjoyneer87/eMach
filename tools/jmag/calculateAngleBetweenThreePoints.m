function angle = calculateAngleBetweenThreePoints(point1, point2, point3)
    % point1, point2, point3는 [x, y] 형식의 2차원 좌표입니다.

    point1=convertXYZData2Array(point1);
    point2=convertXYZData2Array(point2);
    point3=convertXYZData2Array(point3);

  

    % 벡터 1을 계산합니다.
    vector1 = point1 - point2;

    % 벡터 2를 계산합니다.
    vector2 = point3 - point2;

    % atan2 함수를 사용하여 두 벡터 사이의 각도를 계산합니다.
    angle = atan2(norm(cross(vector1, vector2)), dot(vector1, vector2));

    % 라디안 값을 0부터 2*pi 사이로 정규화합니다.
    if angle < 0
        angle = angle + 2 * pi;
    end

    % 라디안 값을 도(degree)로 변환합니다.
    angle = rad2deg(angle);
end
