function area = polyarea3D(x, y, z)
    % 삼각형의 3D 좌표에서 면적을 계산
    v1 = [x(2) - x(1), y(2) - y(1), z(2) - z(1)];
    v2 = [x(3) - x(1), y(3) - y(1), z(3) - z(1)];
    crossProduct = cross(v1, v2);
    area = 0.5 * norm(crossProduct);  % 벡터곱의 크기로 삼각형 면적 계산
end