function surfig=plotSurf2ndPlane(Idvec,fitResult)
% 1. d, q 전류 쌍을 tempSingleDataSet.originDqTable.Id_Peak로부터 가져옴
d_currents=abs(Idvec);
% 2. 각도 범위와 전류 범위 설정
theta = linspace(pi/2, pi, 30); % 0도에서 90도까지
radii = linspace(min(d_currents), max(d_currents), 30); % 전류 범위

% 3. 극좌표에서 카르테시안 좌표로 변환
[d_mesh, q_mesh] = pol2cart(theta', radii);

% 4. TSTotalSurf를 사용하여 z값을 계산
z_values = fitResult(d_mesh, q_mesh);

% 5. 3D surf 플롯 그리기
surfig=surf(d_mesh, q_mesh, z_values, 'EdgeColor', 'none');

% 6. 그래프 라벨 추가
xlabel('d Current');
ylabel('q Current');
zlabel('Z Value');
