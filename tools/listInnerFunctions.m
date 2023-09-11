function listInnerFunctions(funcHandle)
    % Get a list of functions used inside the specified function
    funcInfo = functions(funcHandle);
    subFuncs = funcInfo.functionlist;
    
    if isempty(subFuncs)
        disp(['Function ' func2str(funcHandle) ' does not call any other functions.']);
        return;
    end
    
    disp(['Functions called inside ' func2str(funcHandle) ':']);
    
    for i = 1:length(subFuncs)
        disp(subFuncs{i});
    end
end
