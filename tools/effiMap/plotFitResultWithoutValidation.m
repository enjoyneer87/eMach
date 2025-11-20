function plotFitResultWithoutValidation(fitresult, DataSet, plotDatatype)
    % === 데이터 추출 ===
    xData       = getFieldOrDefault(DataSet, 'xData', []);
    yData       = getFieldOrDefault(DataSet, 'yData', []);
    zData       = getFieldOrDefault(DataSet, 'zData', []);
    varName     = getFieldOrDefault(DataSet, 'varName', 'Unknown');
    originDqTableDesc = getTableDescOrDefault(DataSet, 'originDqTable');

    xlimVals = [min(xData), max(xData)];
    ylimVals = [min(yData), max(yData)];

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


    % === 시각화 유형 ===
    if nargin > 2
        switch plotDatatype
            case 0  % Surface
                [X, Y] = meshgrid(linspace(xlimVals(1), xlimVals(2), 100), ...
                                  linspace(ylimVals(1), ylimVals(2), 100));
                try
                    Z = reshape(predictZ(X(:), Y(:)), size(X));
                catch
                    warning('예측 오류 발생. NaN으로 채움');
                    Z = nan(size(X));
                end
                surf(X, Y, Z); hold on
                plot3(xData, yData, zData, 'bo', 'MarkerFaceColor', 'w');
                hold off
                legend('Interpolation Surface', originDqTableDesc, ...
                       'Location', 'NorthEast', 'Interpreter', 'none');
                xlabel('Id pk[A]'); ylabel('Iq pk[A]'); autoZlabel(varName);
                title(replaceUnderscoresWithSpace(varName)); grid on; formatter_sci

            case 1  % Residual
                try
                    zhat = predictZ(xData, yData);
                    err = zData - zhat;
                catch
                    err = nan(size(zData));
                end
                plot3(xData, yData, err, 'bo', 'MarkerFaceColor', 'w');
                view(-40, 30)
                xlabel('Id pk[A]'); ylabel('Iq pk[A]'); zlabel('Residual');
                title([replaceUnderscoresWithSpace(varName)]);
                grid on; formatter_sci

            case 2  % Contour
                [X, Y] = meshgrid(linspace(xlimVals(1), xlimVals(2), 100), ...
                                  linspace(ylimVals(1), ylimVals(2), 100));
                try
                    Z = reshape(predictZ(X(:), Y(:)), size(X));
                catch
                    warning('Contour 예측 오류 발생. NaN으로 채움');
                    Z = nan(size(X));
                end
                contourf(X, Y, Z, 20); hold on
                plot(xData, yData, 'bo', 'MarkerFaceColor', 'w');
                hold off
                legend('Interpolation Contour', originDqTableDesc, ...
                       'Location', 'NorthEast', 'Interpreter', 'none');
                xlabel('Id pk[A]'); ylabel('Iq pk[A]');
                title(replaceUnderscoresWithSpace(varName)); grid on; formatter_sci

            otherwise
                error('지원되지 않는 plotDatatype입니다.');
        end
    else
        warning('plotDatatype이 지정되지 않았습니다.');
    end
end
