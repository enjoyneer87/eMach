% 피겨를 생성합니다.
figure;

% 예제 데이터 생성 (peaks 함수의 출력 범위 조정)
Z = peaks;
Z = (Z - min(Z(:))) / (max(Z(:)) - min(Z(:))); % 데이터 범위를 0에서 1로 조정
Z = Z * 2; % 데이터 범위를 0에서 2로 조정

% 서피스 플롯 생성
contour(Z);
shading interp; % 서피스의 셰이딩을 보간 모드로 설정

% hsv 컬러맵을 사용하여 필요한 부분만 선택
numColors = 256; % 원하는 색상 단계 수
fullHSV = hsv(numColors); % 전체 HSV 컬러맵 생성

% 0부터 0.85까지의 색상에 해당하는 인덱스 선택 (보라색에서 초록색을 지나 빨간색까지)
selectedHSV = fullHSV(1:round(0.78 * numColors), :);

% 선택한 부분을 반대로 정렬 (보라색에서 빨간색으로)
reversedHSV = flipud(selectedHSV);

% 컬러맵 설정
colormap(reversedHSV);

% 컬러바 설정
c = colorbar;
c.Ticks = linspace(0, 0.8, 11); % 0부터 2까지 21개의 라벨 설정
c.Label.String = 'Colorbar Label'; % 컬러바 라벨

% 제목과 축 라벨 추가
title('Surface Plot with Reversed HSV Colorbar');
xlabel('X-axis');
ylabel('Y-axis');
zlabel('Z-axis');

% 축의 범위를 맞춤
caxis([0 0.8]);

formatter_sci