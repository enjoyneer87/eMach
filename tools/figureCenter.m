% 현재 사용 중인 Matlab 버전에 맞는 디스플레이 크기를 얻어옵니다.
screen_size = get(groot, 'ScreenSize');
% 디스플레이 중앙에 위치하는 figure 창의 x, y 좌표를 계산합니다.
% figure_x = screen_size(3)/2 - 400; % figure 창의 너비가 800으로 가정
% figure_y = screen_size(4)/2 - 300; % figure 창의 높이가 600으로 가정

figure_x = screen_size(3)/2 ; % figure 창의 너비가 800으로 가정
figure_y = screen_size(4)/3 ; % figure 창의 높이가 600으로 가정
% defaultFigurePosition 속성을 변경합니다.
set(groot, 'defaultFigurePosition', [figure_x, figure_y, 800, 600]);