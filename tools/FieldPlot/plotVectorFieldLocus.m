function plotVectorFieldLocus(positionTable, BxMatrix, ByMatrix)
    % plotVectorFieldLocus(positionTable, BxMatrix, ByMatrix)
    % positionTable: 테이블 형식의 위치 데이터, 각 열은 X, Y 좌표를 포함합니다.
    % BxMatrix, ByMatrix: 각 위치에서의 벡터 필드 데이터
    
    % 궤적을 그릴 길이
    numCoordi = size(positionTable, 1);  % 위치 데이터의 수
    numSteps =  size(BxMatrix, 2);      % 벡터 필드 데이터의 수

    % 새 그림 창
    figure;
    hold on;
    axis equal;
    xlabel('X');
    ylabel('Y');
    title('Vector Field Locus');

    % 초기 위치 설정
    xStart = positionTable.PositionX;
    yStart = positionTable.PositionY;
    
    size(xStart)
    % 궤적을 그리기 위한 좌표 초기화
    xLocus = zeros(numCoordi,numSteps);
    yLocus = zeros(numCoordi,numSteps);


    % 초기 locus 설정
    xLocus(:,1) = xStart+ BxMatrix(:, 1);
    yLocus(:,1) = yStart+ ByMatrix(:, 1);

    % % 벡터 필드에 따라 궤적 계산
    size(BxMatrix)
    % for j = 1:numSteps-1
    %     xLocus(:,j+1) = xLocus(:,j) + BxMatrix(:, j+1);
    %     yLocus(:,j+1) = yLocus(:,j) + ByMatrix(:, j+1);
    % end

    for i=2:5:height(ByMatrix)-1
    % plot(PosX(i)+BrMatrix(i,:),PosY(i)+BtMatrix(i,:),'k')
    plot(xStart(i)+BxMatrix(i,:),yStart(i)+ByMatrix(i,:),'k','Marker','+')
    hold on
    end
    scatter(xStart,yStart,'SizeData',5)

    hold off;
end