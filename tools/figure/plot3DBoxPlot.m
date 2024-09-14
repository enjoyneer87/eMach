function plot3DBoxPlot(data, x, y)
data=zData4Box'
x=xData'
y=yData'
    % plot3DBoxPlot - 3D 공간에서 각 위치에 대한 박스플롯을 그리는 함수
    %
    % 입력:
    %   data: 각 위치에 대한 데이터 행렬 (n x m 크기, n은 데이터 개수, m은 위치)
    %   x: x 좌표 (1 x m 크기)
    %   y: y 좌표 (1 x m 크기)

    if nargin < 3
        error('데이터와 x, y 좌표를 모두 제공해야 합니다.');
    end

    % 데이터 열 수가 좌표 크기와 일치하는지 확인
    [n, m] = size(data);
    if length(x) ~= m || length(y) ~= m
        error('x, y 좌표의 크기가 데이터와 일치해야 합니다.');
    end

    % 3D 공간에서 박스플롯 그리기
    figure;
    hold on;

    for i = 1:m
        % 각 좌표에서 데이터의 사분위수를 계산
        q1 = prctile(data(:, i), 25);  % 1사분위
        q2 = prctile(data(:, i), 50);  % 중앙값 (2사분위)
        q3 = prctile(data(:, i), 75);  % 3사분위
        IQR = q3 - q1;  % 사분위 범위
        lowerWhisker = max(min(data(:, i)), q1 - 1.5 * IQR);  % 하위 수염
        upperWhisker = min(max(data(:, i)), q3 + 1.5 * IQR);  % 상위 수염

        % 중앙값 박스 그리기
        fill3([x(i), x(i), x(i)+0.2, x(i)+0.2], ...
              [y(i), y(i), y(i), y(i)], ...
              [q1, q3, q3, q1], 'b', 'FaceAlpha', 0.3);

        % 수염 그리기
        plot3([x(i), x(i)], [y(i), y(i)], [lowerWhisker, q1], 'k');
        plot3([x(i), x(i)], [y(i), y(i)], [q3, upperWhisker], 'k');
        
        % 중앙값 그리기
        plot3([x(i), x(i)+0.2], [y(i), y(i)], [q2, q2], 'r', 'LineWidth', 2);
    end

    xlabel('X');
    ylabel('Y');
    zlabel('Value');
    grid on;
    view(3);
    hold off;
end