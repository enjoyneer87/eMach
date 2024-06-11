function matchingRows2Table = filterMCADTableWithAnyInfo(MCADTable, filterCriteria,FilterVar,filterType)
    if nargin<4
    % Find matching indices for the given filterCriteria
    matchingIndices = findMatchingIndex(MCADTable.(FilterVar), filterCriteria);
    % Filter the table using the matching indices
    matchingRows2Table = MCADTable(matchingIndices, :);
 
    elseif filterType==1 % filterOut
        % switch class(MCADTable.(FilterVar))
            % case 'categorical'
            if iscategorical(MCADTable.(FilterVar))
            col1 = MCADTable.(FilterVar);
            col1=cellstr(col1);            
            isNonMatching = cellfun(@(x) ~any(contains(x, filterCriteria)), col1);                 
            matchingRows2Table = MCADTable(isNonMatching, :);
            matchingRows2Table.(FilterVar)=categorical(matchingRows2Table.(FilterVar));     
            else
            col1 = MCADTable.(FilterVar);
            isNonMatching = cellfun(@(x) ~any(contains(x, filterCriteria)), col1);                 
            matchingRows2Table = MCADTable(isNonMatching, :);    
            end
    end


    
end