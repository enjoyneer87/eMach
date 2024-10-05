function M=cell2matwithvaryCell(C)
%각 배열의 크기 중 최대 크기 찾기
maxLength = max(cellfun(@length, C));

% NaN 또는 0으로 채워 배열 크기를 맞추기 (이 예시에서는 NaN으로 채움)
M = cellfun(@(x) [x; nan(maxLength - length(x), 1)]', C, 'UniformOutput', false);

% 셀 배열을 행렬로 변환 (가로로 결합)
M = cell2mat(M);
end