function cleanedMatrix = removeColumnsWithNaN(matrix)
    % NaN 값을 포함하는 열을 찾기
    nanColumns = any(isnan(matrix), 1);
    
    % NaN 값을 포함하는 열을 제거
    cleanedMatrix = matrix(:, ~nanColumns);
end
