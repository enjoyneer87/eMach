function ResultStructEmagCalc=plotMCADEmagCalc(setGraphName, mcad,FigureData)
    if nargin>2
        if contains(FigureData.PlotType,'Comparison','IgnoreCase',true)  
        LineStyle='--';
        else
        LineStyle='-';
        end
    else
    LineStyle='-';
    end

    ResultStructEmagCalc = struct();
    
     % mcad.SetVariable('TorquePointsPerCycle',60);
    % NumGraphPoints=12;
    if contains(setGraphName,'voltage','IgnoreCase',true)
        YlabelName ='[V]';
    elseif contains(setGraphName,'Terminal','IgnoreCase',true)
        YlabelName ='[V]';
    elseif contains(setGraphName,'Current','IgnoreCase',true)
        YlabelName ='[A]';
    elseif contains(setGraphName,'torque','IgnoreCase',true)
        YlabelName ='[Nm]';
    elseif contains(setGraphName,'ConductorFlux','IgnoreCase',true)
        YlabelName ='B[T]';
    elseif contains(setGraphName,'FluxLinkageOC','IgnoreCase',true)
        YlabelName ='B[T]';
    elseif contains(setGraphName,'FluxLinkage','IgnoreCase',true)
        YlabelName ='[mWb]';
    elseif contains(setGraphName,'Loss','IgnoreCase',true)
        YlabelName ='[W]';
    end

    %% Graph Point Info
    [~, NumGraphPoints] = mcad.GetVariable('TorquePointsPerCycle');
    [~, ShaftSpeed] = mcad.GetVariable('ShaftSpeed');

    %% YvalueName Setting
    % OPpointName = [setGraphName, '@', num2str(ShaftSpeed), 'rpm'];

    List_xvalue = zeros(NumGraphPoints + 1, 1);
    List_valueforGraph = zeros(NumGraphPoints + 1, 1);

    for dataIndex = 0:NumGraphPoints
        [success, x, y] = mcad.GetMagneticGraphPoint(setGraphName, dataIndex);
        if success == 0
            List_xvalue(dataIndex + 1) = x/3;
            List_valueforGraph(dataIndex + 1) = y;
        end
    end
    %% Plot
    plot(List_xvalue, List_valueforGraph, 'LineWidth', 2,'LineStyle',LineStyle)
    a = gca;
    a.XLabel.String = 'ElecAngle[deg]';
    a.YLabel.String = YlabelName;
    xlim([min(List_xvalue), max(List_xvalue)]);
    xticks(0:60:max(List_xvalue));
    title(a,['@',num2str(ShaftSpeed)]);
    
    %% Graph Setting
    setGraphNameNoDigits = regexprep(setGraphName, '\d', ''); % Remove digits
    % titleText = [setGraphNameNoDigits, ' at ', num2str(ShaftSpeed), 'rpm'];
    % title(titleText);

    %% Legend Position
    lgd = legend('Location', 'northoutside','Orientation', 'horizontal',NumColumns=3);
    lgd.Box = 'off'; % 범례의 박스 표시를 없앰
    
    
    % 범례의 위치를 수동으로 조정
    % 예: 범례를 그래프 상단에 더 가깝게 위치시킴
    lgdPos = lgd.Position;
    lgd.Position = [lgdPos(1), lgdPos(2)+lgdPos(4), lgdPos(3), lgdPos(4)];

    formatter_sci
    
    %% Output 
    dataTable = table(List_xvalue, List_valueforGraph, 'VariableNames', {'XValue', 'GraphValue'});
    YValue = max(List_valueforGraph);
    MeanValue = mean(List_valueforGraph);

    ResultStructEmagCalc.dataTable = dataTable;
    ResultStructEmagCalc.MaxValue = YValue;
    ResultStructEmagCalc.meanValue = MeanValue;

    % legend(OPpointName);
end
