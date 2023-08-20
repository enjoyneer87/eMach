function ResultStructEMF=plotBEMFMotorCAD(setGraphName, mcad)
    ResultStructEMF = struct();
    
    [~, NumGraphPoints] = mcad.GetVariable('BackEMFPointsPerCycle');
    [~, ShaftSpeed] = mcad.GetVariable('ShaftSpeed');
    
    OPpointName = [setGraphName, '@', num2str(ShaftSpeed), 'rpm'];
    List_xvalue = zeros(NumGraphPoints + 1, 1);
    List_valueforGraph = zeros(NumGraphPoints + 1, 1);

    for dataIndex = 0:NumGraphPoints
        [success, x, y] = mcad.GetMagneticGraphPoint(setGraphName, dataIndex);
        if success == 0
            List_xvalue(dataIndex + 1) = x;
            List_valueforGraph(dataIndex + 1) = y;
        end
    end
    
    plot(List_xvalue, List_valueforGraph, 'LineWidth', 2)
    a = gca;
    a.XLabel.String = 'ElecAngle';
    a.YLabel.String = 'V';
    xlim([min(List_xvalue), max(List_xvalue)]);
    xticks(0:60:max(List_xvalue));
    
    setGraphNameNoDigits = regexprep(setGraphName, '\d', ''); % Remove digits
    titleText = [setGraphNameNoDigits, ' at ', num2str(ShaftSpeed), 'rpm'];
    title(titleText);

    formatter_sci
    
    dataTable = table(List_xvalue', List_valueforGraph', 'VariableNames', {'XValue', 'GraphValue'});
    YValue = max(List_xvalue);
    ResultStructEMF.ElecAngle = dataTable;
    ResultStructEMF.Value = YValue;
    
    legend(OPpointName);
end

