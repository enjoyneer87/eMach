function length=calcLengthBetweenTwoPoints(point1,point2)
    point1=convertXYZData2Array(point1);
    point2=convertXYZData2Array(point2);
    % 두점사이의 유클리디안 거리
    length = norm(point2-point1);
end