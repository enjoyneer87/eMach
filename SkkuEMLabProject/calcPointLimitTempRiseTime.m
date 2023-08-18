function calcPointLimitTempRiseTime(thermalSettingsTable,mcad)
    % 1) 차량 성능 기준 요구 곡선 OP포인트
    % rpm, torque, 제한온도 지정
    % 2) 전류/전압 조건 기준 OP포인트 해석
    %             - 입력
    %                 온도해석
    %                 최종온도
    % 계산시간 체크 -517sec
    
    
    % Closed Coupled
    % 1) steady-state Iteration
    % 2) Transient Progress
    % 3) 결과 Time
    setMcadTableVariable(thermalSettingsTable,mcad)

    mcad.DoTransientAnalysis()
    
    
    % mcad.SaveTransientTemperatures(TransientTempFileName)
    % mcad.SaveTransientPowerValues(TransientPowerfileName)
    
    % setGraphName = 'Wdg (Average) (C11)';
    % % dataIndex = 0;
    % 
    % [~,NumGraphPoints] = mcad.GetVariable('Last_Transient_Point');
    % 
    % List_xvalue         = zeros(NumGraphPoints+1,1);
    % List_valueforGraph  = zeros(NumGraphPoints+1,1);
    % 
    % for dataIndex = 0:NumGraphPoints
    %     [success, x, y] = mcad.GetTemperatureGraphPoint(setGraphName, dataIndex);
    %     if success == 0
    %         List_xvalue(dataIndex+1) = x;
    %         List_valueforGraph(dataIndex+1) = y;
    %     end
    % end
    % 
    % plot(List_xvalue,List_valueforGraph)
    % 
    % LimitTempTime=max(List_xvalue);

end

