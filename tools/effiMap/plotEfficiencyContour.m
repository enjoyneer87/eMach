function plotEfficiencyContour(speed, torque, efficiency)
    % TN line  추정 
    [speedArray, BorderTorque] = plotMaxTorque(speed, torque);
    speedArray = speedArray';
    BorderTorque = BorderTorque';
    % 등고선 간격과 숨기고자 하는 값 이하의 텍스트 리스트
    cntrs = [92:2:96 96:0.25:round(max(max(efficiency)))];

    % 새로운 x,y 좌표
    speedLinVec = linspace(min(speed), max(speed), 1000);
    torqueLinVec = linspace(min(torque), max(torque), 1000);
    [speedLinVec, torqueLinVec] = meshgrid(speedLinVec, torqueLinVec);
    % z 값을 추정
    effiMapVec = griddata(speed, torque, efficiency, speedLinVec, torqueLinVec);

    %% 측정 위치 scatter
    scatter3(speed, torque, efficiency,'Marker', 'x','DisplayName', 'Measured Point')
    hold on;
    % 2차 등고표면 플롯(surf 대신 contourf with Non EdgeColor) 및 3D 등고선 플롯
    contourf(speedLinVec, torqueLinVec, effiMapVec, 'levels', 0.25, 'EdgeColor', 'none', 'DisplayName', 'Efficiency Contour');
    hold on
    [C, h] = contour3(speedLinVec, torqueLinVec, effiMapVec, cntrs, 'EdgeColor', 'k', 'ShowText', 'on', 'TextStep', 2);
    hold on

    %% TN으로 잘라내기
    patch([speedArray speedArray(end) speedArray(1)], [BorderTorque 1.1*max(BorderTorque) 1.1*max(BorderTorque)], max(efficiency)*ones(1, length(BorderTorque)+2), [1 1 1]); 
    hold on;


    
   
    %% Plot 양식
    caxis([80 100])
    xlabel('Speed, [RPM]'); 
    ylabel('Torque, [Nm]'); 
    set(gcf, 'renderer', 'zbuffer');
    
    %colormap

    % 색상값 범위 설정
    cmin = 0;
    cmax = 1;
    
    % 컬러맵 생성
    n = 256;  % 색상 수
    cmap = jet(n);
    ind = round(1 + (n-1) * (cmax-cmin) / (cmax-cmin+eps));
    cmap = cmap(1:ind,:);
    % 적용 예시
    colormap(cmap)


    % Colorbar 위치 설정
        cb = colorbar('Location', 'eastoutside');
    cb.Label.String = 'Efficiency [%]';

    lg=legend('Measured Point','Efficiency Contour', 'Location', 'northeast');
    % Scientific notation formatter
    formatter_sci;
    view(0,90); % 시야각 조절

end