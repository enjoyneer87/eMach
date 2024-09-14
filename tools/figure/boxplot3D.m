function boxplot3D(data, x, y)
    % boxplot3D - 3D에서 박스플롯 그리기
    % data: 각 위치에 대한 데이터 행렬 (n x m 크기, n은 데이터 개수, m은 위치)
    % x: x 좌표 (박스플롯이 그려질 위치)
    % y: y 좌표 (박스플롯이 그려질 위치)
  % 
  data= data';
  % x =xData'
  % y=yData'   
  % clear q1 q3 upperWhisker lowerWhisker
    % if nargin < 3
    %     error('데이터와 x, y 좌표를 모두 제공해야 합니다.');
    % end

    [n, m] = size(data); % n: 데이터 개수, m: 위치 개수

    if length(x) ~= m || length(y) ~= m
        error('x, y 좌표의 크기가 데이터와 일치해야 합니다.');
    end

    % x좌표 간격을 일정하게 유지하기 위해 위치 조정
    % xPos = linspace(min(x), max(y), m); % 일정한 간격의 x 좌표 설정
    % yPos = linspace(min(y), max(y), m); % 일정한 간격의 x 좌표 설정

    xPos=x'
    yPos=y'
    

    % 각 위치에 대해 boxplot 그리기
    for i = 1:m
        % 기본 boxplot 생성 (일정한 xPos 위치에 생성)
        figure(2)
        bp = boxplot(data(:, i), 'Widths', 50); % 박스 너비 설정
        set(bp, 'Visible', 'off'); % 2D 박스플롯 숨기기

        % 중앙값, 사분위수(Q1, Q3), 수염 계산
        lowerWhisker(1,i) = min(data(:, i));
        upperWhisker(1,i) = max(data(:, i));
        q1(1,i) = quantile(data(:, i), 0.25);
        q3(1,i) = quantile(data(:, i), 0.75);
        medianVal(1,i) = median(data(:, i));
    end
    
    figure(1)
    hold on
        % 수염 (Whiskers)



    % 박스 (Q1 ~ Q3)
    fill3([xPos-10; xPos-10; xPos+10; xPos+10], ...
          [yPos+10; yPos+10; yPos-10; yPos-10], ...
          [q1; q3; q3; q1], 'w','EdgeColor','b');
    hold on
    view(3);

    %%


    for i=1:m
        hold on
        plot3([xPos(i), xPos(i)], [yPos(i), yPos(i)], [lowerWhisker(i), q1(i)], 'k');

        plot3([xPos(i), xPos(i)], [yPos(i), yPos(i)], [q3(i), upperWhisker(i)], 'k');
        % 중앙값
        plot3([xPos(i)-10, xPos(i)+10], [yPos(i)+10, yPos(i)-10], [medianVal(i), medianVal(i)], 'r', 'LineWidth', 2);
        
        % Outliers (if any)
        % % outliers = data(data(:, i) < lowerWhisker | data(:, i) > upperWhisker, i);
        % if ~isempty(outliers)
        %     scatter3(repmat(xPos, size(outliers)), repmat(yPos, size(outliers)), outliers, 'r', 'filled');
        % end
    end
    xlabel('Id pk[A]');
    ylabel('Iq pk[A]');
    zlabel('SCL/REF Ratio');
    grid on;

    hold off;
end