function aq=quiver3Jmag(tr,elementCurl)
% 삼각형 구성 정보 (요소)
triangles = tr.ConnectivityList;
points = tr.Points;

% 각 삼각형 요소의 중심점(centroid) 계산
centroids = incenter(tr);  % 삼각형 중심점 계산 (incenter)


% quiver3를 사용하여 3차원 벡터 필드 플롯 (elementCurl을 벡터 크기로 사용)
% figure;

% 중심점 좌표 (x, y)에서 벡터 그리기
aq=quiver3(centroids(:, 1), centroids(:, 2), zeros(size(centroids, 1), 1), ...  % 벡터 시작점
        elementCurl(:,1), elementCurl(:,2), elementCurl(:,3), ...  % 벡터 방향 (z 방향으로만 표시)
        'AutoScale', 'on', 'LineWidth', 1);  % z 방향으로 크기를 elementCurl 값에 비례하게 표시

% title('3D Vector Field using Element-based Curl');
xlabel('X Position[mm]');
ylabel('Y Position[mm]');
% zlabel('Curl Value (Z)');
view(2);  % 3D 뷰 설정
grid on;
end