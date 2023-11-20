function perpendicularVector = getPerpendicularVector(directionVector)
    % directionVector: 주어진 방향 벡터 [x, y]

    % 주어진 방향 벡터의 수직 벡터를 계산
    perpendicularVector = [-directionVector(2), directionVector(1)];
end
