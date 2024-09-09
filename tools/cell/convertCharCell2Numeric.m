function numericArray = convertCharCell2Numeric(charcell)
%% dev
% tableWithChar=TablesCellCaseRowDataCol{1,2}
% tableWithChar=tableWithChar{1}
    if iscell(charcell)
    numericArray = cellfun(@(x) str2double(x), charcell);      
    end
end


