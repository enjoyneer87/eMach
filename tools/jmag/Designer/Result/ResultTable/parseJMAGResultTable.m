function TablesCellCaseRowDataCol = parseJMAGResultTable(resultTable)
%% dev
% resultTable=resultTableCell{1,1}
% resultTable=probeTableCell{CSVIndex,1}
varName='Var1';

%% `resultTable`에서 `varName` 열에서 'case range' 문자열을 검색합니다.
    RTTableTypeIdx = find(contains(resultTable.(varName), 'case range','IgnoreCase',true));
    RTTableType     =length(RTTableTypeIdx);
    % `separatedTables`는 분리된 테이블들을 담을 셀 배열입니다.
    TablesCellCaseRowDataCol = table();
    % 각 'case range' 구간을 찾고 해당 구간을 별도의 테이블로 분리합니다.

    %% Initia TablesCaseRowDataCol
    startIdx = RTTableTypeIdx(1)-1;
    caseLineIdx  =resultTable(startIdx+1,:);
    CaseList     =removeEmptyCells(caseLineIdx.Variables);
    CaseList     =CaseList(2:end);
    CaseList     =cellfun(@(x) str2num(x),CaseList);
    Numcases     =length(CaseList);
    for caseIndex=1:length(CaseList)
        TablesCellCaseRowDataCol(caseIndex,'Case')={caseIndex};
    end

    %% Table Type Name
    if ~startIdx==0  % from DataSet
       InitDataNameList=resultTable(RTTableTypeIdx-1,1).Variables;
    else  % From Direct Graph
       InitDataNameList=resultTable(RTTableTypeIdx+1,2).Variables;
    end  
    DataNameList = cellfun(@(x) strrep(x, ' ', ''), InitDataNameList, 'UniformOutput', false);  
    DataNameList = cellfun(@(x) strrep(x, '<Value>', ''), DataNameList, 'UniformOutput', false);  
    TablesCellCaseRowDataCol(:,DataNameList)=cell(Numcases,length(DataNameList));
    
    %% 데이터별로 테이블 쪼개기
    % TablePerDataCol=table();
    % TablePerDataCol.TableName=InitDataNameList;
    TablePerDataCol.TableCell=cell(length(InitDataNameList),1);

    %% 각 'case range' 구간을 찾고 해당 구간을 별도의 테이블로 분리합니다.
    for DataIndex = 1:length(RTTableTypeIdx)
        % 현재 'case range' 행의 인덱스
        startIdx = RTTableTypeIdx(DataIndex) ;
        
        % 다음 'case range' 행의 인덱스를 찾습니다.
        if DataIndex < length(RTTableTypeIdx)
            endIdx = RTTableTypeIdx(DataIndex+1) - 2;
        else
            % 마지막 'case range' 이후로는 테이블의 마지막 행까지 선택
            endIdx = height(resultTable);
        end
        
        % 분리된 테이블을 `separatedTables` 셀 배열에 추가합니다.
        % TablePerDataCol{DataIndex,'TableCell'} = {resultTable(startIdx:endIdx, :)};
        emptyVars = varfun(@(x) all(cellfun(@isempty, x)), resultTable(startIdx:endIdx, :) , 'OutputFormat', 'uniform');
        % 비어있는 변수의 인덱스 찾기
        emptyVarIndices = find(emptyVars);
        if ~isempty(emptyVarIndices)
            % 연속적으로 비어있는 인덱스 중 첫 번째만 남기기
            diffIndices = [1, diff(emptyVarIndices)];  % 각 비어있는 인덱스 사이의 차이
            nonConsecutive = [true, diffIndices(2:end) > 1];  % 차이가 1보다 큰 경우만 유지
            emptyVarIndices = emptyVarIndices(nonConsecutive);
        end

        prevIdx = 1;
        %% case-  비어있는 변수를 기준으로 테이블 쪼개기
        for caseIndex = 1:length(emptyVarIndices)
            curIdx                                          = emptyVarIndices(caseIndex);
            TableByCaseByData                               = resultTable(startIdx+1:endIdx, prevIdx:(curIdx-1));
            uniqueColNames                                  = makeUniqueColNames(TableByCaseByData(1,:).Variables);
            TableByCaseByData.Properties.VariableNames      =uniqueColNames;
            TableByCaseByData                               =TableByCaseByData(2:end,:);
            numericTable = convertCharCellTable2Numeric(TableByCaseByData);            
            numericTable  =convertNumTable2TimeTable(numericTable);
            TablesCellCaseRowDataCol(caseIndex,DataIndex+1) = {numericTable};

            prevIdx = curIdx + 1;
             % 마지막 부분 처리
            if prevIdx <= width(numericTable)
                TablesCellCaseRowDataCol(end+1,DataIndex+1) =   {numericTable};
            end
        end
    end
    TablesCellCaseRowDataCol.Properties.RowNames=cellstr(num2str(TablesCellCaseRowDataCol.Case));
    TablesCellCaseRowDataCol=removevars(TablesCellCaseRowDataCol,"Case");
    TablesCellCaseRowDataCol.Properties.DimensionNames=[{'Case'} {'Variables'}];
end

