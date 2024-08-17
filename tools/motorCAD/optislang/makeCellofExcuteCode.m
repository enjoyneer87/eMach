function mcadShouldCode=makeCellofExcuteCode(csvVariableData, mcadCode, inputVariableNames,csvCaseIndex)
    mcadShouldCode={}
    for i = 1:numel(mcadCode)
        for csvVariableIndex = 1:numel(inputVariableNames)
            if contains(mcadCode{i}, inputVariableNames{csvVariableIndex})
                value = csvVariableData.(inputVariableNames{csvVariableIndex})(csvCaseIndex);
                mcadShouldCode{end+1}=strrep(mcadCode{i}, inputVariableNames{csvVariableIndex}, num2str(value))

                %                 
% mcadCode{i} = strrep(mcadCode{i}, inputVariableNames{csvVariableIndex}, num2str(value));
            end
        end
    end
end
