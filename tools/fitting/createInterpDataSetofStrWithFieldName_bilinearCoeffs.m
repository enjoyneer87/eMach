function [fitresult, gof, DataSet,coeffsTable] = createInterpDataSetofStrWithFieldName_bilinearCoeffs(buildDataStr, varName)

    % === 데이터 입력 확인 및 변환 ===
    if istable(buildDataStr)
        inputTable = buildDataStr;
    elseif isstruct(buildDataStr)
        [inputTable, ~] = createTableFromMCADSatuMapStr(buildDataStr);
    else
        error('올바른 데이터를 입력하세요'); 
    end

    % dq 변환 (XGrid/YGrid 범위 산출용 — ZGrid 생성엔 사용 안 함)
    if ~isvarofTable(inputTable, 'Id_Peak')
        [inputTable.Id_Peak, inputTable.Iq_Peak] = pkgamma2dq(inputTable.Is, inputTable.("Current Angle"));
    end

    % varName이 전부 0이면 스킵
    if all(inputTable.(varName) == 0)
        fitresult = []; gof = []; DataSet = []; coeffsTable = [];
        return;
    end

    % === 데이터 준비 (평가용 xData/yData/zData — RMSE 계산에 사용) ===
    [xData, yData, zData] = prepareSurfaceData(inputTable.Id_Peak, inputTable.Iq_Peak, inputTable.(varName));

    % grid 설정
    nx = 255; ny = 255;  % 해상도 설정 (SyRE THOR.mat 기준 255×255)
    xlin = linspace(min(xData), max(xData), nx);
    ylin = linspace(min(yData), max(yData), ny);
    [XGrid, YGrid] = meshgrid(xlin, ylin);

    % === ZGrid 생성: (Is, Gamma) 직사각형 공간에서 보간 → 외삽 없음 ===
    %
    %  Motor-CAD LAB 원본 데이터는 (Is, Gamma) 직사각형 격자
    %  → (Id, Iq)로 변환하면 부채꼴 scattered → 모서리 외삽 발생 (기존 문제)
    %  → (Is, Gamma) 공간에서 interp2 후 각 (Id, Iq) 격자점을 역변환해서 평가
    %    Is  = sqrt(Id² + Iq²)
    %    Gam = atan2d(-Id, Iq)   (Motor-CAD pkgamma2dq 역변환)
    %  → 전류 제한원(Is > Is_max) 바깥 모서리만 NaN → fillmissing으로 처리
    %
    Is_raw  = inputTable.Is;
    Gam_raw = inputTable.("Current Angle");
    Z_raw   = inputTable.(varName);

    [Is_u,  ~, Is_idx]  = unique(Is_raw);
    [Gam_u, ~, Gam_idx] = unique(Gam_raw);

    nIs = numel(Is_u);  nGam = numel(Gam_u);

    if nIs * nGam == numel(Z_raw)
        % (Is, Gamma) 직사각형 격자 확인 → 행렬로 조립
        Z_mat = zeros(nGam, nIs);
        for k = 1:numel(Z_raw)
            Z_mat(Gam_idx(k), Is_idx(k)) = Z_raw(k);
        end

        % 각 (Id, Iq) 격자점을 (Is, Gamma)로 역변환 후 interp2 평가
        Is_q  = sqrt(XGrid.^2 + YGrid.^2);   % Peak 전류 크기
        Gam_q = atan2d(-XGrid, YGrid);         % Motor-CAD gamma 규약 역변환

        ZGrid = interp2(Is_u, Gam_u, Z_mat, Is_q, Gam_q, 'linear', NaN);
        ZGrid = fillmissing(ZGrid, 'nearest'); % 전류 제한원 바깥 NaN 처리
    else
        % 비정형 데이터 → 기존 scatteredInterpolant fallback
        warning('createInterp:notRectGrid', ...
            '[%s] (Is,Gamma) 격자가 직사각형이 아님 → scatteredInterpolant 사용', varName);
        F = scatteredInterpolant(xData, yData, zData, 'linear', 'linear');
        ZGrid = F(XGrid, YGrid);
    end

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
