function [fitresult, gof, DataSet,coeffsTable] = createInterpDataSetofStrWithFieldName_bilinearCoeffs(buildDataStr, varName)

    % === 데이터 입력 확인 및 변환 ===
    if istable(buildDataStr)
        inputTable = buildDataStr;
    elseif isstruct(buildDataStr)
        [inputTable, ~] = createTableFromMCADSatuMapStr(buildDataStr);
    else
        error('올바른 데이터를 입력하세요'); 
    end

    % dq 변환
    if ~isvarofTable(inputTable, 'Id_Peak')
        [inputTable.Id_Peak, inputTable.Iq_Peak] = pkgamma2dq(inputTable.Is, inputTable.("Current Angle"));
    end

    % varName이 전부 0이면 스킵
    if all(inputTable.(varName) == 0)
        fitresult = []; gof = []; DataSet = []; coeffsTable = [];
        return;
    end

    % === 데이터 준비 ===
    [xData, yData, zData] = prepareSurfaceData(inputTable.Id_Peak, inputTable.Iq_Peak, inputTable.(varName));
    
    % grid 설정
    nx = 100; ny = 100;  % 해상도 설정
    xlin = linspace(min(xData), max(xData), nx);
    ylin = linspace(min(yData), max(yData), ny);
    [XGrid, YGrid] = meshgrid(xlin, ylin);

    % 보간 표면 생성 (외삽 포함)
    F = scatteredInterpolant(xData, yData, zData, 'linear', 'linear');
    ZGrid = F(XGrid, YGrid);

    % === bilinear 계수 추출 ===
    coeffList = nan((nx - 1)*(ny - 1), 5);  % 미리 공간 할당
    idx = 1;

    for i = 1:nx - 1
        x1 = xlin(i);   x2 = xlin(i+1);
        for j = 1:ny - 1
            y1 = ylin(j);   y2 = ylin(j+1);

            % 해당 셀의 4점 값
            z11 = ZGrid(j, i);
            z12 = ZGrid(j+1, i);
            z21 = ZGrid(j, i+1);
            z22 = ZGrid(j+1, i+1);

            % NaN 체크
            if any(isnan([z11, z12, z21, z22]))
                continue;
            end

            % 계수 계산
            A = [1 x1 y1 x1*y1;
                 1 x1 y2 x1*y2;
                 1 x2 y1 x2*y1;
                 1 x2 y2 x2*y2];
            b = [z11; z12; z21; z22];
            coeffs = A \ b;

            % 최대 전류값
            Imax = max([hypot(x1, y1), hypot(x2, y2)]);
            coeffList(idx, :) = [coeffs(:)', Imax];
            idx = idx + 1;
        end
    end

    % NaN 행 제거
    coeffList = coeffList(~any(isnan(coeffList), 2), :);

    % 테이블 생성
    coeffsTable = array2table(coeffList, ...
        'VariableNames', {'a00','a10','a01','a11','Imax'});

    % === 보간 함수 생성 ===
    fitresult = @(x, y) interp2(XGrid, YGrid, ZGrid, x, y, 'linear', NaN);

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
    DataSet.residual = zData - zhat;
    DataSet.originDqTable.Properties.Description = 'Training Data';
    DataSet.coeffsTable = coeffsTable;

end
