function zhat = evaluateRBFThinplate(x, y, centers, weights, coeffs)
% evaluateRBFThinplate - RBF Thin Plate Spline 모델을 사용하여 예측
%
% 입력:
%   x, y - 예측할 위치의 좌표 (스칼라, 벡터, 또는 행렬)
%   centers - RBF 중심점들 [N x 2] 행렬 (N개의 [x, y] 좌표)
%   weights - RBF 가중치 벡터 [N x 1]
%   coeffs - 선형 계수 벡터 [3 x 1] (상수, x계수, y계수)
%
% 출력:
%   zhat - 예측된 값 (x, y와 같은 크기)

    % 입력 크기 저장 (나중에 원래 형태로 복원하기 위해)
    original_size = size(x);
    
    % 입력 검증
    if any(size(x) ~= size(y))
        error('x와 y의 크기가 일치하지 않습니다.');
    end
    
    if size(centers, 2) ~= 2
        error('centers는 [N x 2] 행렬이어야 합니다.');
    end
    
    if length(weights) ~= size(centers, 1)
        error('weights의 길이는 centers의 행 수와 일치해야 합니다.');
    end
    
    if length(coeffs) ~= 3
        error('coeffs는 길이 3의 벡터여야 합니다.');
    end
    
    % NaN 입력값 처리
    nan_mask = isnan(x) | isnan(y);
    if any(nan_mask(:))
        fprintf('경고: 입력에 %d개의 NaN 값이 있습니다.\n', sum(nan_mask(:)));
    end
    
    % 예측할 위치들을 행렬로 변환
    XY = [x(:), y(:)];  % [M x 2] 형태로 변환
    M = size(XY, 1);    % 예측 점의 개수
    
    % weights와 coeffs의 NaN 검사
    if any(isnan(weights)) || any(isnan(coeffs))
        error('모델 파라미터에 NaN 값이 포함되어 있습니다. 모델을 다시 훈련해야 합니다.');
    end
    
    % 중심점들과의 거리 계산
    R = pdist2(XY, centers);  % [M x N] 거리 행렬
    
    % Thin Plate Spline 기저 함수 계산 (안정성 개선)
    Phi = zeros(size(R));
    non_zero_idx = R > eps;  % 0에 가까운 값들 처리
    
    if any(non_zero_idx(:))
        Phi(non_zero_idx) = R(non_zero_idx).^2 .* log(R(non_zero_idx));
    end
    
    % 선형 보정 항 계산
    P = [ones(M, 1), XY];  % [M x 3] 행렬: [1, x, y]
    
    % 최종 예측값 계산
    try
        zhat = Phi * weights + P * coeffs;
    catch ME
        error('예측 계산 중 오류 발생: %s', ME.message);
    end
    
    % NaN 값 검증
    if any(isnan(zhat))
        fprintf('경고: 예측 결과에 %d개의 NaN 값이 생성되었습니다.\n', sum(isnan(zhat)));
        % NaN이 있는 위치를 입력 NaN 위치로 설정
        zhat(nan_mask(:)) = NaN;
    end
    
    % 원래 입력 형태로 복원
    zhat = reshape(zhat, original_size);
end
