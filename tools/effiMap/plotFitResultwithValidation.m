function plotFitResultwithValidation(fitresult, DataSet,plotDatatype)
%%
    % 플롯 생성
    xData              =DataSet.xData        ;
    yData              =DataSet.yData        ;
    zData              =DataSet.zData        ;
    xValidation        =DataSet.xValidation  ;    
    yValidation        =DataSet.yValidation  ;    
    zValidation        =DataSet.zValidation  ;    
    varName            =DataSet.varName      ;
    statics            =DataSet.statics      ;
   originDqTable.Properties.Description=    DataSet.originDqTable.Properties.Description          ;    
   ValidationDqTable.Properties.Description=    DataSet.ValidationDqTable.Properties.Description ;
    % figure('Name', varName);
    xlim = [min([xData; xValidation]), max([xData; xValidation])];
    ylim = [min([yData; yValidation]), max([yData; yValidation])];

    if nargin>2
        switch plotDatatype
            case 0
            % figure(1)
            a = plot(fitresult, [xData, yData], zData, 'XLim', xlim, 'YLim', ylim);
            hold on
            a(end+1) = plot3(xValidation, yValidation, zValidation, 'bo', 'MarkerFaceColor', 'w');
            hold off            
            legend(a, 'Interpolation Surface', [originDqTable.Properties.Description], [ValidationDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');
            xlabel('Id', 'Interpreter', 'none');
            ylabel('Iq', 'Interpreter', 'none');
            autoZlabel(varName)
            title([replaceUnderscoresWithSpace(varName)]);
            grid on
            formatter_sci
            case 1
            % 잔차 플로팅.
            % figure(2)
            % b = plot(fitresult, [xData, yData], zData, 'Style', 'Residual', 'XLim', xlim, 'YLim', ylim);
            hold on
            b = plot3(xValidation, yValidation, zValidation - fitresult(xValidation, yValidation), 'bo', 'MarkerFaceColor', 'w');
            % legend(b,['Absolute Error',newline,originDqTable.Properties.Description,'-',ValidationDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');

            % b = plot3(xValidation, yValidation, (zValidation - fitresult(xValidation, yValidation))./zValidation, 'bo', 'MarkerFaceColor', 'w');
            % legend(b,['Relative Error',newline,originDqTable.Properties.Description,'-',ValidationDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');

            view(-40, 30)
            % b = contourf(xValidation, yValidation, zValidation - fitresult(xValidation, yValidation), 'bo', 'MarkerFaceColor', 'w');
            % b(end+1) = plot3(xValidation, yValidation, zValidation - fitresult(xValidation, yValidation), 'bo', 'MarkerFaceColor', 'w');
            hold off
            % legend(b,[ValidationDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');
            % legend(b, [originDqTable.Properties.Description], [ValidationDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');
            xlabel('Id', 'Interpreter', 'none');
            ylabel('Iq', 'Interpreter', 'none');
            zlabel('Absolute Error', 'Interpreter', 'none');
            title([replaceUnderscoresWithSpace(varName), newline,'RMSE=',num2str(statics.rmse)]);
            grid on
            formatter_sci
            case 2
            % 등고선 플롯을 만드십시오.
            % figure(3)
            c = plot(fitresult, [xData, yData], zData, 'Style', 'Contour', 'XLim', xlim, 'YLim', ylim);
            hold on
            c(end+1) = plot(xValidation, yValidation, 'bo', 'MarkerFaceColor', 'w');
            hold off
            legend(c, 'Interpolation Surface', [originDqTable.Properties.Description], [ValidationDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');
            xlabel('Id', 'Interpreter', 'none');
            ylabel('Iq', 'Interpreter', 'none');
            title([replaceUnderscoresWithSpace(varName)]);
            grid on
            formatter_sci
        end
    else
            figure(1)
            h = plot(fitresult, [xData, yData], zData, 'XLim', xlim, 'YLim', ylim);
            hold on
            h(end+1) = plot3(xValidation, yValidation, zValidation, 'bo', 'MarkerFaceColor', 'w');
            hold off
            legend(h, 'Interpolation Surface', [originDqTable.Properties.Description], [ValidationDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');
            xlabel('Id', 'Interpreter', 'none');
            ylabel('Iq', 'Interpreter', 'none');
            zlabel(replaceUnderscoresWithSpace(varName), 'Interpreter', 'none');
            grid on
            formatter_sci
            % 잔차 플로팅.
            figure(2)
            % h = plot(fitresult, [xData, yData], zData, 'Style', 'Residual', 'XLim', xlim, 'YLim', ylim);
            hold on
            b = plot3(xValidation, yValidation, zValidation - fitresult(xValidation, yValidation), 'bo', 'MarkerFaceColor', 'w');
            
            % b(end+1) = plot3(xValidation, yValidation, zValidation - fitresult(xValidation, yValidation), 'bo', 'MarkerFaceColor', 'w');
            hold off
            legend(b,['Absolute Error',newline,originDqTable.Properties.Description,'-',ValidationDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');
            % legend(h, [originDqTable.Properties.Description], [ValidationDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');
            xlabel('Id', 'Interpreter', 'none');
            ylabel('Iq', 'Interpreter', 'none');
            zlabel([replaceUnderscoresWithSpace(varName), ' residual'], 'Interpreter', 'none');
            grid on
            formatter_sci
            % 등고선 플롯을 만드십시오.
            figure(3)
            h = plot(fitresult, [xData, yData], zData, 'Style', 'Contour', 'XLim', xlim, 'YLim', ylim);
            hold on
            h(end+1) = plot(xValidation, yValidation, 'bo', 'MarkerFaceColor', 'w');
            hold off
            legend(h, 'Interpolation Surface', [originDqTable.Properties.Description], [ValidationDqTable.Properties.Description], 'Location', 'NorthEast', 'Interpreter', 'none');
            xlabel('Id', 'Interpreter', 'none');
            ylabel('Iq', 'Interpreter', 'none');
            grid on
            formatter_sci
    end
end