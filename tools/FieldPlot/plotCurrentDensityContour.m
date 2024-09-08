function plotCurrentDensityContour(elementCenters, currentDensity)
    % plotCurrentDensityContour - 요소 중심 위치와 전류 밀도 값을 기반으로 전류 밀도 컨투어 플롯을 생성합니다.
    %
    % 입력:
    %   elementCenters - 요소 중심 좌표 (Mx2 또는 Mx3 행렬, M은 요소 수)
    %   currentDensity - 요소 중심에서의 전류 밀도 값 (Mx1 벡터, M은 요소 수)
    %
    % 예:
    %   plotCurrentDensityContour(elementCenters, currentDensity);

    % 입력이 2D인 경우만 다루는 예시

    % 
    % elementCenters=elementPos
    % currentDensity=EddyLoss
    % elementCenters=WireStruct(SlotIndex).NodeTable.nodeCoords
    currentDensity=WireStruct(SlotIndex).JnodeTable
    if size(elementCenters, 2) ~= 2
        error('현재 2D 좌표계만 지원합니다.');
    end

    % 요소 중심 좌표에서 x, y 좌표 분리
    x = elementCenters(:, 1);
    y = elementCenters(:, 2);

    % 삼각형 그리드 만들기 (Delaunay 삼각화 사용)
    tri = delaunay(x, y);

    % 전류 밀도 컨투어 플롯
    figure;
    trisurf(tri, x, y, currentDensity(1,:).Variables', 'EdgeColor', 'none'); % 삼각형 요소 그리기
    view(2);  % 2D로 보기
    colorbar; % 컬러바 추가
    colormap jet;  % 컬러맵 설정
    shading interp; % 셰이딩 방식 설정
    title('Current Density Contour');
    xlabel('X Position');
    ylabel('Y Position');
end