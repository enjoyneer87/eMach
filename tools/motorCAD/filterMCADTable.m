function matchingTable = filterMCADTable(MCADTable,filterCriteria,findType,varargin)
    % Initialize filtered table with the original MCADTable
    filteredNameTable = MCADTable;
    if nargin>2
        checkType=checkfindType(findType);
    else
        checkType=0;
    end
%%
    if nargin>3
        if varargin{1}==1
            filterType=1;      
        % Apply each filter criteria
            filteredNameTable = filterMCADAutomationNameTable(filteredNameTable, filterCriteria,checkType);           
            if nargin>4
                for i = 2:numel(varargin)
                    filteredNameTable = filterMCADAutomationNameTable(filteredNameTable, varargin{i});
                end
            end       
            matchingTable = getTableNonMatchingRowsBetweenTwoTable(MCADTable, 'AutomationName', filteredNameTable, 'AutomationName');
        elseif varargin{1}==0
            filterType=0;      
         % Apply each filter criteria
            filteredNameTable = filterMCADAutomationNameTable(filteredNameTable, filterCriteria,checkType);
            if nargin>4
                for i = 2:numel(varargin)
                    filteredNameTable = filterMCADAutomationNameTable(filteredNameTable, varargin{i});
                end
            end      
            matchingTable = getTableMatchingRowsBetweenTwoTable(MCADTable, 'AutomationName', filteredNameTable, 'AutomationName');
        else
            filterType=0;                
            filteredNameTable = filterMCADAutomationNameTable(filteredNameTable, filterCriteria,checkType);
            if nargin>4
                for i = 2:numel(varargin)
                    filteredNameTable = filterMCADAutomationNameTable(filteredNameTable, varargin{i});
                end
            end     
            % Apply each filter criteria
            matchingTable = getTableMatchingRowsBetweenTwoTable(MCADTable, 'AutomationName', filteredNameTable, 'AutomationName');
        end
     %%
    else
        filterType=0; % 0 is contains, 1 is filterout
        filteredNameTable = filterMCADAutomationNameTable(filteredNameTable, filterCriteria,checkType);
        matchingTable = getTableMatchingRowsBetweenTwoTable(MCADTable, 'AutomationName', filteredNameTable, 'AutomationName');       
    end

end
