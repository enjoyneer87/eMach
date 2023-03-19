function [uniqueSpeed, maxTorque]=plotMaxTorque(speedArray, torqueArray)
    % 각 속도에서의 최대 토크값 계산
    [uniqueSpeed, ~, idx] = unique(round(speedArray,-1));  % 속도 범위를 0.1 단위로 정규화한 후 unique 값 추출
    maxTorque = accumarray(idx, torqueArray, [], @max);  % 각 속도에서의 최대 토크값 추출

    % 각 속도에서의 최대 토크값으로 이루어진 선 그래프 생성
    plot(uniqueSpeed, maxTorque,LineStyle="-",Marker="*");
%     xlabel('Speed, RPM');
%     ylabel('Torque, N*m');
%     title('Max Torque vs. Speed');
end