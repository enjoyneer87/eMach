function corrected_surface = correctSurfByBilinearInterp(surface, x_range, y_range, new_points)
    % 기존 곡면과 보정할 새로운 네 개의 포인트를 입력받아 bilinear interpolation 방식으로 보정
    
    % surface: 기존의 곡면 (2D matrix)
    % x_range: 기존 곡면의 x 좌표 범위 (예: [x_min, x_max])
    % y_range: 기존 곡면의 y 좌표 범위 (예: [y_min, y_max])
    % new_points: 보정할 새로운 포인트 (4x3 matrix)
    %   각 행은 [x, y, value] 형식으로, 네 개의 새로운 포인트를 나타냄
    
    % 새로운 포인트 4개
    x1 = new_points(1, 1);
    y1 = new_points(1, 2);
    v1 = new_points(1, 3);
    
    x2 = new_points(2, 1);
    y2 = new_points(2, 2);
    v2 = new_points(2, 3);
    
    x3 = new_points(3, 1);
    y3 = new_points(3, 2);
    v3 = new_points(3, 3);
    
    x4 = new_points(4, 1);
    y4 = new_points(4, 2);
    v4 = new_points(4, 3);
    
    % 기존 곡면의 크기 가져오기
    [rows, cols] = size(surface);
    
    % x와 y 좌표를 생성
    x_vals = linspace(x_range(1), x_range(2), cols);
    y_vals = linspace(y_range(1), y_range(2), rows);
    
    % 보정된 곡면 초기화
    corrected_surface = surface;
    
    % bilinear interpolation 계산을 위해 격자 내 좌표별로 보정값을 계산
    for i = 1:rows
        for j = 1:cols
            % 현재 좌표
            x = x_vals(j);
            y = y_vals(i);
            
            % bilinear interpolation 공식 적용
            denom = (x2 - x1) * (y3 - y1);  % x2 != x1, y3 != y1 이어야 함
            if denom == 0
                % 보정 불가
                error('Invalid points for bilinear interpolation.');
            end
            
            % bilinear interpolation 값 계산
            interp_value = (v1 * (x2 - x) * (y3 - y) + ...
                            v2 * (x - x1) * (y3 - y) + ...
                            v3 * (x2 - x) * (y - y1) + ...
                            v4 * (x - x1) * (y - y1)) / denom;
                        
            % 보정된 값을 기존 surface에 추가
            corrected_surface(i, j) = surface(i, j) + interp_value;
        end
    end
end