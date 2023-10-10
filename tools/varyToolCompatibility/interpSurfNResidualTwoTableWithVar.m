function [fitresult, gof, DataSet] = interpSurfNResidualTwoTableWithVar(originDqTable, ValidationDqTable, varName)
    % 매개변수로 전달된 varName에 대한 검증
    if ~isvarofTable(originDqTable, varName)
        error('The given variable name does not exist in the originDqTable.');
    end
    if ~isvarofTable(ValidationDqTable, varName)
        error('The given variable name does not exist in the ValidationDqTable.');
    end

    % 데이터 준비
    [xData, yData, zData] = prepareSurfaceData(originDqTable.Id_Peak, originDqTable.Iq_Peak, originDqTable.(varName));
    [xValidation, yValidation, zValidation] = prepareSurfaceData(ValidationDqTable.Id_Peak, ValidationDqTable.Iq_Peak, ValidationDqTable.(varName));

    % fittype과 옵션 설정
    % ft = 'cubicinterp';
    % ft='smoothingspline'
    ft='cubicinterp';
    % CubicSplineInterpolant
    opts = fitoptions('Method', 'CubicSplineInterpolant');
    opts.ExtrapolationMethod = 'linear';
    % opts = fitoptions('Method', 'BiharmonicInterpolant');
    % opts = fitoptions('Method', 'NonlinearLeastSquares');
    % opts.ExtrapolationMethod = 'auto';
    % opts.ExtrapolationMethod = 'biharmonic';
    % opts.Normalize = 'on';
    [fitresult, gof] = fit([xData, yData], zData, ft, opts);

    % 검증 데이터와 비교
    residual = zValidation - fitresult(xValidation, yValidation);
    statics.nNaN = nnz(isnan(residual));
    residual(isnan(residual)) = [];
    statics.sse = norm(residual)^2;
    statics.rmse = sqrt(statics.sse/length(residual));
    fprintf('''%s'' 피팅에 대한 검증의 적합도:\n', varName);
    fprintf('    SSE : %f\n', statics.sse);
    fprintf('    RMSE : %f\n', statics.rmse);
    fprintf('    데이터 영역 밖에 %i개의 점이 있습니다.\n', statics.nNaN);
    DataSet.originDqTable.Properties.Description            =   originDqTable.Properties.Description             ;
    DataSet.ValidationDqTable.Properties.Description        =   ValidationDqTable.Properties.Description     ;

    DataSet.xData=xData;
    DataSet.yData=yData;
    DataSet.zData=zData;
    DataSet.xValidation=xValidation;
    DataSet.yValidation=yValidation;
    DataSet.zValidation=zValidation;
    DataSet.varName=varName;
    DataSet.statics=statics;

end