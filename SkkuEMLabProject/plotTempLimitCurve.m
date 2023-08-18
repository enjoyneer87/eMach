function ResultStructLimitTempRise =plotTempLimitCurve(setGraphName,mcad)
    ResultStructLimitTempRise=struct();
    % setGraphName = 'Wdg (Average) (C11)';
    
    [~,NumGraphPoints] = mcad.GetVariable('Last_Transient_Point');
    
    List_xvalue         = zeros(NumGraphPoints+1,1);
    List_valueforGraph  = zeros(NumGraphPoints+1,1);
    
    for dataIndex = 0:NumGraphPoints
        [success, x, y] = mcad.GetTemperatureGraphPoint(setGraphName, dataIndex);
        if success == 0
            List_xvalue(dataIndex+1) = x;
            List_valueforGraph(dataIndex+1) = y;
        end
    end
    
    plot(List_xvalue,List_valueforGraph)
    dataTable = table(List_xvalue', List_valueforGraph', 'VariableNames', {'XValue', 'GraphValue'});
    LimitTempTime=max(List_xvalue);
    ResultStructLimitTempRise.TempRiseCurve=dataTable;
    ResultStructLimitTempRise.LimitTempTime=LimitTempTime;

end