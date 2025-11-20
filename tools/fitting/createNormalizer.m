function [normalizeXY, scaler] = createNormalizer(DataSet)
    % 입력 데이터 확인
    x = DataSet.xData;
    y = DataSet.yData;

    % 기본값 설정
    scaler = struct();

    if isfield(DataSet, 'scaler') && isfield(DataSet.scaler, 'mu') && isfield(DataSet.scaler, 'sigma')
        % 기존 정규화 정보 사용
        mu = DataSet.scaler.mu;
        sigma = DataSet.scaler.sigma;
    elseif ~isempty(x) && ~isempty(y)
        % 자동 계산
        mu = [mean(x(:), 'omitnan'), mean(y(:), 'omitnan')];
        sigma = [std(x(:), 'omitnan'), std(y(:), 'omitnan')];
        sigma(sigma == 0) = 1;  % 분산이 0일 경우 대비
    else
        % 입력이 없는 경우 정규화 생략
        mu = [0, 0];
        sigma = [1, 1];
    end

    % 정규화 함수 정의
    normalizeXY = @(x, y) deal((x - mu(1)) ./ sigma(1), (y - mu(2)) ./ sigma(2));

    % scaler 정보 반환
    scaler.mu = mu;
    scaler.sigma = sigma;
end
