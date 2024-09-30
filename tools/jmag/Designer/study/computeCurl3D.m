function elementCurl = computeCurl3D(TR, u, v, w)
    % tr: triangulation 객체 (삼각형 또는 3D 요소 정보 포함)
    % u: 각 노드에서의 벡터 필드의 x 성분
    % v: 각 노드에서의 벡터 필드의 y 성분
    % w: 각 노드에서의 벡터 필드의 z 성분
    
    % 삼각형의 연결 정보 가져오기
    triangles = TR.ConnectivityList;
    points = mm2m(TR.Points);  % 각 노드의 좌표 (x, y, z)
    
    % 요소 중심에서의 curl 값을 저장할 배열
    elementCurl = zeros(size(triangles, 1), 3);  % x, y, z 방향의 curl 값 저장
    
    % 각 삼각형 요소에 대해 curl 계산
    for i = 1:size(triangles, 1)
        % 삼각형의 노드 인덱스 가져오기
        nodeIndices = triangles(i, :);
        
        % 삼각형을 이루는 각 꼭짓점의 좌표
        x = points(nodeIndices, 1);
        y = points(nodeIndices, 2);
        Dim=size(points);
        if Dim(2)<3
        z= zeros(len(y),1);
        else
        z = points(nodeIndices, 3);
        end
        % 해당 삼각형을 이루는 각 꼭짓점에서의 u, v, w 값
        u_vals = u(nodeIndices);
        v_vals = v(nodeIndices);
        w_vals = w(nodeIndices);
        
        % 삼각형 요소에서의 curl 계산
        % 삼각형의 면적 계산 (벡터곱으로 면적 구함)
        area = polyarea3D(x, y, z);
        
        % 편미분 근사 계산
        dv_dz = (v_vals(2) - v_vals(1)) * (z(3) - z(1)) + (v_vals(3) - v_vals(1)) * (z(2) - z(1));
        du_dy = (u_vals(2) - u_vals(1)) * (y(3) - y(1)) + (u_vals(3) - u_vals(1)) * (y(2) - y(1));
        dw_dx = (w_vals(2) - w_vals(1)) * (x(3) - x(1)) + (w_vals(3) - w_vals(1)) * (x(2) - x(1));
        dw_dy = (w_vals(2) - w_vals(1)) * (y(3) - y(1)) + (w_vals(3) - w_vals(1)) * (y(2) - y(1));
        du_dz = (u_vals(2) - u_vals(1)) * (z(3) - z(1)) + (u_vals(3) - u_vals(1)) * (z(2) - z(1));
        dv_dx = (v_vals(2) - v_vals(1)) * (x(3) - x(1)) + (v_vals(3) - v_vals(1)) * (x(2) - x(1));
        
        % curl 성분 계산 (x, y, z 방향)
        curl_x = (dw_dy - dv_dz) / (2 * area);
        curl_y = (du_dz - dw_dx) / (2 * area);
        curl_z = (dv_dx - du_dy) / (2 * area);
        
        % curl 결과 저장
        elementCurl(i, :) = [curl_x, curl_y, curl_z];
    end
end