function plotJMAGResultDataStruct(DataSetTable,var2Plot,StepData)
%% devTemp
% DataSetTable=ResultTable
% stepData=StepData
% DataSetTable.Properties.Description

% for dataIndex=1:length(AllResultDataStruct)
    % table2Plot=AllResultDataStruct(dataIndex).dataTable;
    % titleName=AllResultDataStruct(dataIndex).DataName;


% DataSetTable=TablesCellCaseRowDataCol{1,2}
%%
if ~istable(DataSetTable)
    if iscell(DataSetTable)
        DataSetTable=DataSetTable{1};
    end    
end

    %% Figure
    % figure(dataIndex)
    % if contains(titleName,'Iron Loss')
    if contains(DataSetTable.Properties.VariableNames,'Iron Loss')
    plot1DFFT(table2Plot)
    else
        if nargin>2
            plotTransientTable(DataSetTable,var2Plot,StepData)
        elseif nargin>1
            plotTransientTable(DataSetTable,var2Plot)
        else
            plotTransientTable(DataSetTable)
        end
    end
    % title(titleName);    
    % hold off
% end

end