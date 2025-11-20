function plotFitResultwithValidation(fitresult, DataSet, plotDatatype)
    % === 데이터 추출 ===
    xData       = getFieldOrDefault(DataSet, 'xData', []);
    yData       = getFieldOrDefault(DataSet, 'yData', []);
    zData       = getFieldOrDefault(DataSet, 'zData', []);
    xValidation = getFieldOrDefault(DataSet, 'xValidation', []);
    yValidation = getFieldOrDefault(DataSet, 'yValidation', []);
    zValidation = getFieldOrDefault(DataSet, 'zValidation', []);
    varName     = getFieldOrDefault(DataSet, 'varName', 'Unknown');
    originDqTableDesc     = getTableDescOrDefault(DataSet, 'originDqTable');
    ValidationDqTableDesc = getFieldOrDefault(DataSet, 'ValidationDqTable', 'Validation');
    
    % === 예측 함수 래핑 ===
    if isa(fitresult, 'function_handle')
        predictZ = @(x, y) fitresult(x, y);
    elseif isa(fitresult, 'cfit') || isa(fitresult, 'sfit') || isa(fitresult, 'curve') || isa(fitresult, 'surface')
        predictZ = @(x, y) feval(fitresult, x, y);  % 또는 fitresult(x, y)도 가능
    elseif isa(fitresult, 'curvefit.model.ThinPlateSpline') && ismethod(fitresult, 'evaluate')
        predictZ = @(x, y) fitresult.evaluate([x(:), y(:)]);
    else
        error('지원되지 않는 fitresult 타입입니다.');
    end

    xlimVals = [min(DataSet.XGrid(:)), max(DataSet.XGrid(:))];
    ylimVals = [min(DataSet.YGrid(:)), max(DataSet.YGrid(:))];

    % === 시각화 분기 ===
    switch plotDatatype
        case 0  % Surface plot
            [X, Y] = meshgrid(linspace(xlimVals(1), xlimVals(2), 100), ...
                              linspace(ylimVals(1), ylimVals(2), 100));
            try
                Z = reshape(predictZ(X, Y), size(X));
            catch
                warning('예측 오류 발생. NaN으로 채움');
                Z = nan(size(X));
            end

            % NaN 체크
            if all(isnan(Z), 'all')
                warning('예측 Z값이 모두 NaN입니다. 보간 범위를 확인하세요.');
            end

            surf(X, Y, Z); shading interp
            hold on
            plot3(xData, yData, zData, 'bo', 'MarkerFaceColor', 'w');
            if ~isempty(xValidation)
                plot3(xValidation, yValidation, zValidation, 'ro', 'MarkerFaceColor', 'w');
            end
            hold off
            legend('Interpolated Surface', originDqTableDesc, ValidationDqTableDesc, ...
                   'Location', 'NorthEast', 'Interpreter', 'none');
            xlabel('Id pk[A]'); ylabel('Iq pk[A]'); autoZlabel(varName);
            title(replaceUnderscoresWithSpace(varName));
            grid on; formatter_sci

        case 1  % Residual plot
            if isempty(xValidation)
                warning('Validation 데이터가 없어 잔차 플롯을 생략합니다.');
                return;
            end
            try
                zhat = predictZ(xValidation, yValidation);
                err = zValidation - zhat;
            catch
                err = nan(size(zValidation));
                warning('예측 오류로 잔차 계산 실패');
            end

            plot3(xValidation, yValidation, err, 'ro', 'MarkerFaceColor', 'w');
            view(-40, 30)
            xlabel('Id pk[A]'); ylabel('Iq pk[A]'); zlabel('Residual [z - ẑ]');
            title([replaceUnderscoresWithSpace(varName), newline, 'Validation Residual']);
            grid on; formatter_sci

        case 2  % Contour plot
            [X, Y] = meshgrid(linspace(xlimVals(1), xlimVals(2), 100), ...
                              linspace(ylimVals(1), ylimVals(2), 100));
            try
                Z = reshape(predictZ(X(:), Y(:)), size(X));
            catch
                Z = nan(size(X));
            end
            contourf(X, Y, Z, 30); hold on
            if ~isempty(xValidation)
                plot(xValidation, yValidation, 'ro', 'MarkerFaceColor', 'w');
            end
            hold off
            legend('Interpolation Contour', originDqTableDesc, ValidationDqTableDesc, ...
                   'Location', 'NorthEast', 'Interpreter', 'none');
            xlabel('Id pk[A]'); ylabel('Iq pk[A]');
            title(replaceUnderscoresWithSpace(varName));
            grid on; formatter_sci

        otherwise
            error('plotDatatype는 0 (surf), 1 (residual), 2 (contour) 중 하나여야 합니다.');
    end
end
