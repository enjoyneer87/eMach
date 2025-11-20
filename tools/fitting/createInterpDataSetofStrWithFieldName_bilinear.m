function [fitresult, gof, DataSet] = createInterpDataSetofStrWithFieldName_bilinear(buildDataStr, varName)

    % === 데이터 입력 확인 및 변환 ===
    if istable(buildDataStr)
        inputTable = buildDataStr;
    elseif isstruct(buildDataStr)
        [inputTable, ~] = createTableFromMCADSatuMapStr(buildDataStr);
    else
        error('올바른 데이터를 입력하세요');
    end

    % dq 변환이 없으면 수행
    if ~isvarofTable(inputTable, 'Id_Peak')
        [inputTable.Id_Peak, inputTable.Iq_Peak] = pkgamma2dq(inputTable.Is, inputTable.("Current Angle"));
    end

    % varName이 전부 0이면 스킵
    if all(inputTable.(varName) == 0)
        fitresult = [];
        gof = [];
        DataSet = [];
        return;
    end

    % === 데이터 준비 ===
    [xData, yData, zData] = prepareSurfaceData(inputTable.Id_Peak, inputTable.Iq_Peak, inputTable.(varName));

    % === 중복 제거 (평균으로 병합) ===
    T = table(xData, yData, zData);
    T = varfun(@mean, T, 'GroupingVariables', {'xData', 'yData'});
    xData = T.xData;
    yData = T.yData;
    zData = T.mean_zData;

    % === 보간 함수 생성 ===
    F = scatteredInterpolant(xData, yData, zData, 'linear', 'none');  % 외삽은 none → NaN 반환
    fitresult = @(x, y) F(x, y);

    % === RMSE 계산 ===
    zhat = fitresult(xData, yData);
    residual = zData - zhat;
    residual(isnan(residual)) = [];  % 외삽된 NaN 제거
    rmse = sqrt(mean(residual.^2, 'omitnan'));

    gof.rsquare = NaN;  % R²는 계산 안 함
    gof.rmse = rmse;

    % === 데이터셋 구성 ===
    DataSet.originDqTable = inputTable;
    DataSet.xData = xData;
    DataSet.yData = yData;
    DataSet.zData = zData;
    DataSet.varName = varName;
    DataSet.originDqTable.Properties.Description = 'Training Data';

end
