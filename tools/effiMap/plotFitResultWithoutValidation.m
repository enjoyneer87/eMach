function plotFitResultWithoutValidation(fitresult, DataSet,plotDatatype)
%%
    % 플롯 생성
    xData              =DataSet.xData        ;
    yData              =DataSet.yData        ;
    zData              =DataSet.zData        ;
    varName            =DataSet.varName      ;
    originDqTable.Properties.Description=    DataSet.originDqTable.Properties.Description          ;    
    % figure('Name', varName);
    xlim = [min(xData), max(xData)];
    ylim = [min(yData), max(yData)];

    if nargin>2
        switch plotDatatype
            case 0
            % figure(1)
            a = plot(fitresult, [xData, yData], zData, 'XLim', xlim, 'YLim', ylim);
            hold on
            hold off            
            legend(a, 'Interpolation Surface', [originDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');
            xlabel('Id pk[A]', 'Interpreter', 'none');
            ylabel('Iq pk[A]', 'Interpreter', 'none');
            autoZlabel(varName)
            title([replaceUnderscoresWithSpace(varName)]);
            grid on
            formatter_sci
            case 1
            % 잔차 플로팅.
            % figure(2)
            b = plot(fitresult, [xData, yData], zData, 'Style', 'Residual', 'XLim', xlim, 'YLim', ylim);
            hold on
            % legend(b,['Relative Error',newline,originDqTable.Properties.Description,'-',ValidationDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');

            view(-40, 30)
            hold off
            xlabel('Id pk[A]', 'Interpreter', 'none');
            ylabel('Iq pk[A]', 'Interpreter', 'none');
            zlabel('Residual', 'Interpreter', 'none');
            title(replaceUnderscoresWithSpace(varName));
            % title([replaceUnderscoresWithSpace(varName), newline,'RMSE=',num2str(statics.rmse)]);
            grid on
            formatter_sci
            case 2
            % 등고선 플롯을 만드십시오.
            % figure(3)
            c = plot(fitresult, [xData, yData], zData, 'Style', 'Contour', 'XLim', xlim, 'YLim', ylim);
            hold on
            hold off
            legend(c, 'Interpolation Surface', [originDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');
            xlabel('Id pk[A]', 'Interpreter', 'none');
            ylabel('Iq pk[A]', 'Interpreter', 'none');
            title([replaceUnderscoresWithSpace(varName)]);
            grid on
            formatter_sci
        end
    else
            figure(1)
            h = plot(fitresult, [xData, yData], zData, 'XLim', xlim, 'YLim', ylim);
            hold on
            hold off
            legend(h, 'Interpolation Surface', [originDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');
            xlabel('Id pk[A]', 'Interpreter', 'none');
            ylabel('Iq pk[A]', 'Interpreter', 'none');
            zlabel(replaceUnderscoresWithSpace(varName), 'Interpreter', 'none');
            grid on
            formatter_sci
            % 잔차 플로팅.
            figure(2)
            h = plot(fitresult, [xData, yData], zData, 'Style', 'Residual', 'XLim', xlim, 'YLim', ylim);
            hold on
            
            hold off
            xlabel('Id pk[A]', 'Interpreter', 'none');
            ylabel('Iq pk[A]', 'Interpreter', 'none');
            zlabel([replaceUnderscoresWithSpace(varName), ' residual'], 'Interpreter', 'none');
            grid on
            formatter_sci
            % 등고선 플롯을 만드십시오.
            figure(3)
            h = plot(fitresult, [xData, yData], zData, 'Style', 'Contour', 'XLim', xlim, 'YLim', ylim);
            hold on
            hold off
            xlabel('Id pk[A]', 'Interpreter', 'none');
            ylabel('Iq pk[A]', 'Interpreter', 'none');
            grid on
            formatter_sci
    end
end