function [fitresult, gof, DataSet] = createInterpDataSetofStrWithFieldName_interp2(buildDataStr, varName)

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
    
    % 고유 좌표 추출 → uniform grid로 대체
    xlin = linspace(min(xData), max(xData), 100);  % 또는 적절한 해상도
    ylin = linspace(min(yData), max(yData), 100);
    [XGrid, YGrid] = meshgrid(xlin, ylin);
    
    % ZGrid는 scatteredInterpolant을 통해 계산
    F = scatteredInterpolant(xData, yData, zData, 'linear', 'none');
    ZGrid = F(XGrid, YGrid);  % Grid에 대해 보간값 계산\
     


    % === 보간 함수 생성 (interp2는 X, Y의 열 방향이 x축, 행 방향이 y축)
    fitresult = @(x, y) interp2(XGrid, YGrid, ZGrid, x, y, 'linear', NaN);  % 외삽은 NaN

    % === RMSE 계산 ===
    zhat = fitresult(xData, yData);
    residual = zData - zhat;
    residual(isnan(residual)) = [];
    rmse = sqrt(mean(residual.^2, 'omitnan'));

    % === 출력 구조 ===
    gof.rsquare = NaN;
    gof.rmse = rmse;

    DataSet.originDqTable = inputTable;
    DataSet.xData = xData;
    DataSet.yData = yData;
    DataSet.zData = zData;
    DataSet.varName = varName;
    DataSet.XGrid = XGrid;
    DataSet.YGrid = YGrid;
    DataSet.ZGrid = ZGrid;
    DataSet.originDqTable.Properties.Description = 'Training Data';

end
