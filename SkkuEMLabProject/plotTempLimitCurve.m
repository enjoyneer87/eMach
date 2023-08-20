function ResultStructLimitTempRise = plotTempLimitCurve(setGraphName, OPpointName, mcad)
    ResultStructLimitTempRise = struct();
    [~, NumGraphPoints] = mcad.GetVariable('Last_Transient_Point');

    % Create empty matrices to store data
    List_xvalues = zeros(NumGraphPoints + 1, length(setGraphName));
    List_valuesForGraph = zeros(NumGraphPoints + 1, length(setGraphName));

    for graphIndex = 1:length(setGraphName)
        for dataIndex = 0:NumGraphPoints
            [success, x, y] = mcad.GetTemperatureGraphPoint(setGraphName{graphIndex}, dataIndex);
            if success == 0
                List_xvalues(dataIndex + 1, graphIndex) = x;
                List_valuesForGraph(dataIndex + 1, graphIndex) = y;
            end
        end
        plot(List_xvalues(:, graphIndex), List_valuesForGraph(:, graphIndex))
        hold on
    end

    a = gca;
    a.XLabel.String = 'Time [sec]';
    a.YLabel.String = 'Temperature [°C]';
    legend(setGraphName)
    title(OPpointName);
    formatter_sci

    hold off

    % Create a table with data from List_valuesForGraph and List_xvalues
    tempRiseTable = array2table([List_xvalues, List_valuesForGraph], 'VariableNames', [setGraphName, strcat(setGraphName, '_Temp')]);
    ResultStructLimitTempRise.TempRiseCurve = tempRiseTable;
    ResultStructLimitTempRise.LimitTempTime = max(List_xvalues(:, 1)); % Using time from the first graph
end
