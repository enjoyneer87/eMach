function [fitresult,gof,DataSet]=createValidationDataSetTwoStrWithFieldName(buildDataStr1,buildDataStr2,varName)

    [fitresult, gof, DataSet] = createInterpDataSetofStrWithFieldName(buildDataStr1, varName);
    [~, ~, DataSetValidation] = createInterpDataSetofStrWithFieldName(buildDataStr2, varName);
    isEmptyResult = isempty(fitresult) && isempty(gof) && isempty(DataSet) || isempty(DataSetValidation);

    if ~isEmptyResult
        xValidation                =DataSetValidation.xData;
        yValidation                =DataSetValidation.yData;
        zValidation                =DataSetValidation.zData;
        
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
        
        %% DataSet에 검증데이터도 포함
        DataSet.xValidation=xValidation;
        DataSet.yValidation=yValidation;
        DataSet.zValidation=zValidation;
        DataSet.statics=statics;
        DataSet.ValidationDqTable=DataSetValidation.originDqTable;
    else
        fitresult=[];
        gof=[];
        DataSet=[];
    end
end