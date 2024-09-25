function numericTable = convertCharCellTable2Numeric(tableWithChar)
%% dev
% tableWithChar=TablesCellCaseRowDataCol{1,2}
% tableWithChar=tableWithChar{1}
%%
if ~istable(tableWithChar)
    if iscell(tableWithChar)
        tableWithChar=tableWithChar{1};
    end
end


    % 모든 변수에 대해 char형 셀 배열을 숫자형 배열로 변환
    numericTable = varfun(@(x) strrep(x,'"',''), tableWithChar,'OutputFormat','table');
    numericTable = varfun(@(x) str2double(x), numericTable,'OutputFormat','table');
end

