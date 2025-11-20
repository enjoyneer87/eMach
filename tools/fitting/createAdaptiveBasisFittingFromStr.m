function [coeffVector, basisFunc, DataSet] = createAdaptiveBasisFittingFromStr(buildDataStr, varName)
    if istable(buildDataStr)
        inputTable = buildDataStr;
    elseif isstruct(buildDataStr)
        [inputTable, ~] = createTableFromMCADSatuMapStr(buildDataStr);
    else 
        error('입력은 table 또는 struct이어야 합니다.');
    end

    if ~isvarofTable(inputTable, 'Id_Peak')
        [inputTable.Id_Peak, inputTable.Iq_Peak] = pkgamma2dq(inputTable.Is, inputTable.("Current Angle"));
    end

    if all(inputTable.(varName) == 0)
        coeffVector = [];
        basisFunc = [];
        DataSet = [];
        return;
    end

    % 데이터 준비
    [xData, yData, zData] = prepareSurfaceData(inputTable.Id_Peak, inputTable.Iq_Peak, inputTable.(varName));

    % 표준화
    mu = mean([xData, yData], 1);
    sigma = std([xData, yData], 0, 1);
    sigma(sigma == 0) = 1;  % 분산 0 방지

    xNorm = (xData - mu(1)) ./ sigma(1);
    yNorm = (yData - mu(2)) ./ sigma(2);

    degreesToTry = 2:4;
    bestRMSE = inf;
    bestDegree = 2;
    bestCoeff = [];
    bestPhi = [];

    for d = degreesToTry
        Phi = createPolyBasis(xNorm, yNorm, d);
        coeffs = Phi \ zData;
        zPred = Phi * coeffs;
        rmse = sqrt(mean((zData - zPred).^2));

        if rmse < bestRMSE
            bestRMSE = rmse;
            bestDegree = d;
            bestCoeff = coeffs;
            bestPhi = Phi;
        end
    end

    coeffVector = bestCoeff;

    % Basis function 핸들
    basisFunc = @(xq, yq) createPolyBasis( ...
        (xq - mu(1)) ./ sigma(1), ...
        (yq - mu(2)) ./ sigma(2), ...
        bestDegree) * coeffVector;

    % 결과 패키징
    DataSet.xData = xData;
    DataSet.yData = yData;
    DataSet.zData = zData;
    DataSet.varName = varName;
    DataSet.statics.rmse = bestRMSE;
    DataSet.originDqTable = inputTable;
    DataSet.originDqTable.Properties.Description = 'Training Data';
    DataSet.ValidationDqTable = inputTable;  % 향후 교차검증 확장 가능
    DataSet.ValidationDqTable.Properties.Description = 'Used as Training';

    % 메타정보
    DataSet.basis.mu = mu;
    DataSet.basis.sigma = sigma;
    DataSet.basis.degree = bestDegree;
    
end

function Phi = createPolyBasis(x, y, degree)
    % 입력: x, y는 column vector (Nx1), degree는 정수
    % 출력: Phi는 NxM의 basis 행렬

    if size(x,2) > 1; x = x(:); end
    if size(y,2) > 1; y = y(:); end
    N = length(x);

    % Basis 함수 생성
    terms = [];
    for i = 0:degree
        for j = 0:i
            xi = x.^(i-j);
            yj = y.^j;
            terms = [terms, xi .* yj];
        end
    end

    Phi = terms;
end
