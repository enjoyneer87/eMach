function errorMap= fcnCompareMapContour(contour1Measured,contour2Simulation)
%%두개의 sturct data를 입력으로 해야합니다.
% contour 데이터 읽어들이기
% contour1Measured = load('contour1.mat');
% contour2Simulation = load('contour2.mat');
% contour1Measured.z
% contour2Simulation.z=Efficiency;
% contour 데이터 크기 확인

size1 = size(contour1Measured.z);
size2 = size(contour2Simulation.z);

% contour 데이터 크기가 다르다면 크기를 맞춰주기 위해 보간
if ~isequal(size1, size2)
    % 보간 좌표 생성
    xi = linspace(min([contour1Measured.x(:); contour2Simulation.x(:)]), max([contour1Measured.x(:); contour2Simulation.x(:)]), 100);
    yi = linspace(min([contour1Measured.y(:); contour2Simulation.y(:)]), max([contour1Measured.y(:); contour2Simulation.y(:)]), 100);
    [XI, YI] = meshgrid(xi, yi);
    
    % contour 데이터 보간
    ZI1 = griddata(contour1Measured.x, contour1Measured.y, contour1Measured.z, XI, YI, 'cubic');
    ZI2 = griddata(contour2Simulation.x, contour2Simulation.y, contour2Simulation.z, XI, YI, 'cubic');
else
    XI = contour1Measured.x;
    YI = contour1Measured.y;
    ZI1 = contour1Measured.z;
    ZI2 = contour2Simulation.z;
end

% contour 데이터 비교를 위한 차이 계산
error = (ZI1 - ZI2);
errorMap.x=XI;
errorMap.y=YI;
errorMap.z=error;
end