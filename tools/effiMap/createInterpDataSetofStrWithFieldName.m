function [fitresult, gof, DataSet] = createInterpDataSetofStrWithFieldName(buildDataStr, varName)
    % 매개변수로 전달된 varName에 대한 검증
    % if ~isvarofTable(InputTable, varName)
    %     error('The given variable name does not exist in the originDqTable.');
    % end
    if istable(buildDataStr)
        inputTable=buildDataStr;
    elseif isstruct(buildDataStr)
    [inputTable,~] = createTableFromMCADSatuMapStr(buildDataStr);
    else 
        error('올바른 데이터를 입력하세요');
    end
    % if ~isvarofTable(ValidationDqTable, varName)
    %     error('The given variable name does not exist in the ValidationDqTable.');
    % end

    if ~isvarofTable(inputTable,'Id_Peak')
        [inputTable.Id_Peak, inputTable.Iq_Peak]=pkbeta2dq(inputTable.Is, inputTable.("Current Angle"));
    end
    % 데이터 준비
    
    if ~(all(inputTable.(varName)==0))
    [xData, yData, zData] = prepareSurfaceData(inputTable.Id_Peak, inputTable.Iq_Peak, inputTable.(varName));
    % [xValidation, yValidation, zValidation] = prepareSurfaceData(ValidationDqTable.Id_Peak, ValidationDqTable.Iq_Peak, ValidationDqTable.(varName));
    
    % fittype과 옵션 설정
    % ft = 'cubicinterp';
    % ft='smoothingspline'
    ft='thinplate';
    % CubicSplineInterpolant
    opts = fitoptions('Method', 'thinplate');
    % opts = fitoptions('Method', 'CubicSplineInterpolant');
    % opts.ExtrapolationMethod = 'linear';
    % opts = fitoptions('Method', 'BiharmonicInterpolant');
    % opts = fitoptions('Method', 'NonlinearLeastSquares');
    opts.ExtrapolationMethod = 'auto';
    % opts.ExtrapolationMethod = 'biharmonic';
    % opts.Normalize = 'on';
    [fitresult, gof] = fit([xData, yData], zData, ft, opts);

    % 검증 데이터와 비교
    % residual = zValidation - fitresult(xValidation, yValidation);
    % statics.nNaN = nnz(isnan(residual));
    % residual(isnan(residual)) = [];
    % statics.sse = norm(residual)^2;
    % statics.rmse = sqrt(statics.sse/length(residual));
    % fprintf('''%s'' 피팅에 대한 검증의 적합도:\n', varName);
    % fprintf('    SSE : %f\n', statics.sse);
    % fprintf('    RMSE : %f\n', statics.rmse);
    % fprintf('    데이터 영역 밖에 %i개의 점이 있습니다.\n', statics.nNaN);
    % DataSet.originDqTable.Properties.Description            =   InputTable.Properties.Description             ;
    % DataSet.ValidationDqTable.Properties.Description        =   ValidationDqTable.Properties.Description     ;
    DataSet.originDqTable=inputTable;
    DataSet.xData=xData;
    DataSet.yData=yData;
    DataSet.zData=zData;
    % DataSet.xValidation=xValidation;
    % DataSet.yValidation=yValidation;
    % DataSet.zValidation=zValidation;
    DataSet.varName=varName;
    % DataSet.statics=statics; 
    else 
        fitresult=[];
        DataSet=[];
        gof=[];
    end
end