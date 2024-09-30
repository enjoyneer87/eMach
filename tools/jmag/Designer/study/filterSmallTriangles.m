function [filtered_triangles, areas] = filterSmallTriangles(DT, threshold)
    % filterSmallTriangles - 주어진 점 집합에서 DelaunayTriangulation을 수행하고,
    %                        지정된 임계값(threshold) 이하의 면적을 가진 삼각형을 제거
    %
    % 입력:
    %   P - 점 집합 (N x 2 행렬)
    %   threshold - 면적 임계값 (이 값보다 작은 면적의 삼각형을 제거)
    %
    % 출력:
    %   filtered_triangles - 필터링된 삼각형의 Connectivity List
    %   areas - 각 삼각형의 면적
    
    % DelaunayTriangulation 생성
    
    % 삼각형의 Connectivity List 추출
    triangles = DT.ConnectivityList;
    
    % 각 삼각형의 세 점 좌표 추출
    X1 = DT.Points(triangles(:,1), 1);
    Y1 = DT.Points(triangles(:,1), 2);
    X2 = DT.Points(triangles(:,2), 1);
    Y2 = DT.Points(triangles(:,2), 2);
    X3 = DT.Points(triangles(:,3), 1);
    Y3 = DT.Points(triangles(:,3), 2);
    
    % 삼각형의 면적 계산
    areas = 0.5 * abs(X1.*(Y2 - Y3) + X2.*(Y3 - Y1) + X3.*(Y1 - Y2));
    
    % 면적이 임계값보다 큰 삼각형만 선택
    large_triangles = areas > threshold;
    
    % 필터링된 삼각형의 Connectivity List 반환
    filtered_triangles = triangles(large_triangles, :);
    
    % 필터링된 삼각형 개수 출력
    % disp(['필터링 후 삼각형 개수: ', num2str(size(filtered_triangles, 1))]);
end