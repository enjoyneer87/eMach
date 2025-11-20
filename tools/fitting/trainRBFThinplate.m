function [rbfFunc, weights, coeffs, centers] = trainRBFThinplate(IdVec, IqVec, zVec)
% trainRBFThinplate - RBF Thin Plate Spline 모델 훈련
%
% 입력:
%   IdVec - Id 값들의 벡터
%   IqVec - Iq 값들의 벡터  
%   zVec - 목표 값들의 벡터 (손실, 자속 등)
%
% 출력:
%   rbfFunc - 예측 함수 핸들
%   weights - RBF 가중치
%   coeffs - 선형 계수
%   centers - RBF 중심점들

    % 입력 데이터 검증 및 전처리
    IdVec = IdVec(:);
    IqVec = IqVec(:);
    zVec = zVec(:);
    
    % NaN 값 제거
    valid_idx = ~(isnan(IdVec) | isnan(IqVec) | isnan(zVec));
    IdVec = IdVec(valid_idx);
    IqVec = IqVec(valid_idx);
    zVec = zVec(valid_idx);
    
    % 중복점 제거 (같은 위치에 다른 값이 있는 경우 평균값 사용)
    [unique_coords, ~, idx] = unique([IdVec, IqVec], 'rows', 'stable');
    if length(unique_coords) < length(IdVec)
        % 중복된 좌표에 대해 평균값 계산
        unique_z = accumarray(idx, zVec, [], @mean);
        IdVec = unique_coords(:, 1);
        IqVec = unique_coords(:, 2);
        zVec = unique_z;
    end
    
    % 최소 데이터 포인트 확인
    N = length(IdVec);
    if N < 4
        error('최소 4개의 데이터 포인트가 필요합니다. 현재: %d개', N);
    end
    
    % === 중심점 ===
    centers = [IdVec, IqVec];

    % === 거리 행렬 및 RBF 행렬 ===
    R = pdist2(centers, centers);          % NxN 거리행렬
    
    % Thin Plate Spline 기저 함수 (안정성 개선)
    Phi = zeros(size(R));
    non_zero_idx = R > eps;
    Phi(non_zero_idx) = R(non_zero_idx).^2 .* log(R(non_zero_idx));
    
    % 정규화 추가 (수치적 안정성 향상)
    lambda = 1e-8 * trace(Phi) / N;  % 적응적 정규화 파라미터
    Phi = Phi + lambda * eye(N);

    % === 선형 항 (affine term) ===
    P = [ones(N,1), IdVec, IqVec];
    
    % === 시스템 구성 (확장된 형태) ===
    A = [Phi, P;
         P', zeros(3,3)];
    b = [zVec; zeros(3,1)];
    
    % === 행렬 조건수 확인 및 해결 ===
    cond_A = cond(A);
    if cond_A > 1e12 || isnan(cond_A) || isinf(cond_A)
        % 조건수가 너무 나쁘면 더 강한 정규화 적용
        fprintf('경고: 행렬 조건수가 나쁩니다 (%.2e). 정규화를 강화합니다.\n', cond_A);
        
        % 더 강한 정규화
        lambda_strong = 1e-4 * trace(Phi) / N;
        Phi_reg = Phi - lambda * eye(N) + lambda_strong * eye(N);  % 기존 정규화 제거 후 강화
        
        A = [Phi_reg, P;
             P', zeros(3,3)];
        
        % 다시 조건수 확인
        cond_A_new = cond(A);
        if cond_A_new > 1e12 || isnan(cond_A_new) || isinf(cond_A_new)
            % 여전히 문제가 있으면 pinv 사용
            fprintf('경고: 정규화 후에도 조건수가 나쁩니다. pseudo-inverse를 사용합니다.\n');
            w = pinv(A) * b;
        else
            w = A \ b;
        end
    else
        % === 일반적인 해 계산 ===
        try
            w = A \ b;
        catch ME
            fprintf('경고: 직접 해법 실패. pseudo-inverse를 사용합니다. 오류: %s\n', ME.message);
            w = pinv(A) * b;
        end
    end
    
    % === 결과 검증 ===
    if any(isnan(w)) || any(isinf(w))
        error('계산된 가중치에 NaN 또는 Inf 값이 포함되어 있습니다. 데이터를 확인해주세요.');
    end
    
    weights = w(1:N);
    coeffs = w(N+1:end);
    
    % === 예측 함수 ===
    rbfFunc = @(x, y) evaluateRBFThinplate(x, y, centers, weights, coeffs);
    
    % === 훈련 성능 확인 (선택사항) ===
    if nargout == 0  % 출력이 요청되지 않으면 성능 출력
        pred_train = rbfFunc(IdVec, IqVec);
        train_rmse = sqrt(mean((zVec - pred_train).^2));
        fprintf('훈련 RMSE: %.6f\n', train_rmse);
    end
end


