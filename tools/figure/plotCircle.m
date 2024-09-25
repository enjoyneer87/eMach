function [x,y]=plotCircle(radius,thetaRange,color,lineStyle)

if nargin<2
    theta = linspace(0, 2*pi, 100); % 0부터 2*pi까지 100개의 점으로 나누기
else
    theta = linspace(thetaRange(1), thetaRange(2), 100);
end
if nargin<4
    lineStyle='-';
end
% 원의 방정식에 따라 x, y 좌표 생성
x = radius * cos(theta); % x 좌표
y = radius * sin(theta); % y 좌표

% 원 그리기
% figure; % 새로운 그림 창 생성
if nargin>2
    plot(x, y, 'LineWidth', 2,'Color',color,'LineStyle',lineStyle); % 생성한 x, y 좌표로 원 그리기
else
    plot(x, y, 'LineWidth', 2,'LineStyle',lineStyle); % 생성한 x, y 좌표로 원 그리기
end
axis equal; % x축과 y축의 스케일을 동일하게 설정하여 원이 왜곡되지 않도록 함
grid on; % 격자 표시 켜기
% xlabel('X-Axis'); % x축 레이블

end