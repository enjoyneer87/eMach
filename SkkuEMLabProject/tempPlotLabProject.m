function tempPlotLabProject(dataIndex,DesignNumber,fileDir,DataName,matFilePath,maxrpm,kW,baserpm,Imax_rms_MotorLab,PhaseAdvance,RMSCurrentDensity,DCvoltage,ActiveTurn,Length_Calc_Lab)
    figure(dataIndex)
    if strcmpi(DataName,'Effi map')
    [MatFileData]=plotEfficiencyMotorcad(matFilePath);
    elseif strcmpi(DataName,'Copper Loss')
    [MatFileData]=plotAnyContourByNameinMotorcad(matFilePath,'Stator_Copper_Loss');
    else 
        [MatFileData]=plotAnyContourByNameinMotorcad(matFilePath,DataName);
    end
    hold on
    [baseTorque,MaxspeedTorque]=plotTNcurvebyBasePoint(baserpm, maxrpm, kW);
    fig = gcf; % Get the current figure
    
    
    % Set the new size using the Position property
    newPosition = [fig.Position(1), fig.Position(2), 1000, 800];
    %% Additional info
    text(baserpm, baseTorque, sprintf('%.2f Nm @ %d RPM with %.2f A_{rms}@ %.2f deg', baseTorque, baserpm,Imax_rms_MotorLab,PhaseAdvance), 'VerticalAlignment', 'bottom', 'FontName', 'Times New Roman');
    CurrentLimit=sprintf('%.2f', Imax_rms_MotorLab);
    currentDensity=sprintf('%.2f', RMSCurrentDensity);
    
    fig.Position = newPosition; % Update the figure's position and size
    % title([DesignNumber{1}, ' Effimap']);
    title([DesignNumber{1}, strrep(DataName,'_',' ')]);
    
    
    % 범례 아래에 텍스트 추가
    line1 =  ['I=',num2str(CurrentLimit),'A_{rms} Limit (J_{rms}=',num2str(currentDensity),')'] ;
    line2 =  [' V_{DC}=',num2str(DCvoltage)];
    line3= [' StackLength=',num2str(Length_Calc_Lab),' Active Turns=', num2str(ActiveTurn)];
    legend_str = sprintf('%s\n%s\n%s', line1, line2,line3);
    
    lgd = legend;
    % lgd.Position(2) = lgd.Position(2); % 범례 위치 조정
    text(lgd.Position(1)+0.05, lgd.Position(2), legend_str, 'Units', 'normalized', 'HorizontalAlignment', 'left', 'VerticalAlignment', 'bottom','FontName', 'Times New Roman');
    title(['Design89 ', 'Effimap', ' I=',num2str(CurrentLimit),'A_{rms} Limit']);
    % set(gcf, 'Visible', 'on'); % figure의 Visible 속성을 'off'로 설정
    lgd.String={strrep(DataName,'_',' '),'Required TN'};
    saveFigures2png(fileDir);
    % close all
end