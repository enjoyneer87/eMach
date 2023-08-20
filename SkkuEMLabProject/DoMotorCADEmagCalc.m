function ResultStructEmagCalc=DoMotorCADEmagCalc(setGraphName, mcad)
    ResultStructEmagCalc = struct();
    
     % mcad.SetVariable('TorquePointsPerCycle',60);
    % NumGraphPoints=12;
    if contains(setGraphName,'voltage','IgnoreCase',true)
        YlabelName ='[V]';
    elseif contains(setGraphName,'Terminal','IgnoreCase',true)
        YlabelName ='[V]';
    elseif contains(setGraphName,'torque','IgnoreCase',true)
        YlabelName ='[Nm]';
    end

    % OperatingPointParameters_Lab
    [~,LabOpPoint_ShaftTorque]              =mcad.GetVariable('LabOpPoint_ShaftTorque');
    [~,LabOpPoint_StatorCurrent_Phase_Peak] =mcad.GetVariable('LabOpPoint_StatorCurrent_Phase_Peak');
    [~,LabOpPoint_PhaseAdvance]             =mcad.GetVariable('LabOpPoint_PhaseAdvance');

    % mcad.DoMagneticCalculation()

    %
    [~, NumGraphPoints] = mcad.GetVariable('TorquePointsPerCycle');
    [~, ShaftSpeed] = mcad.GetVariable('ShaftSpeed');

    % 
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
    a.XLabel.String = 'ElecAngle[deg]';
    a.YLabel.String = YlabelName;
    xlim([min(List_xvalue), max(List_xvalue)]);
    xticks(0:60:max(List_xvalue));
    
    setGraphNameNoDigits = regexprep(setGraphName, '\d', ''); % Remove digits
    titleText = [setGraphNameNoDigits, ' at ', num2str(ShaftSpeed), 'rpm'];
    title(titleText);

    formatter_sci
    
    dataTable = table(List_xvalue, List_valueforGraph, 'VariableNames', {'XValue', 'GraphValue'});
    YValue = max(List_valueforGraph);
    MeanValue = mean(List_valueforGraph);

    ResultStructEmagCalc.dataTable = dataTable;
    ResultStructEmagCalc.MaxValue = YValue;
    ResultStructEmagCalc.meanValue = MeanValue;

    legend(OPpointName);
end
