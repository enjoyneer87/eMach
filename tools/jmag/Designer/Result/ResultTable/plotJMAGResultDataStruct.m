function plotJMAGResultDataStruct(DataSetTable)

% DataSetTable.Properties.Description

% for dataIndex=1:length(AllResultDataStruct)
    % table2Plot=AllResultDataStruct(dataIndex).dataTable;
    % titleName=AllResultDataStruct(dataIndex).DataName;
    %% Figure
    % figure(dataIndex)
    % if contains(titleName,'Iron Loss')
    if contains(DataSetTable.Properties.VariableNames,'Iron Loss')
    plot1DFFT(table2Plot)
    else
    plotTransientTable(DataSetTable)
    
    end
    % title(titleName);    
    hold off
% end

end