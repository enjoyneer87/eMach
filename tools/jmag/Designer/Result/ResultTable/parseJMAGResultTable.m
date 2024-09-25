function TablesCellCaseRowDataCol = parseJMAGResultTable(resultTable)
%% dev

    % resultTable=resultTableCell{15,1}
    % resultTable=ResultTableFromCSVPerStudy
    % TablesCellCaseRowDataCol
    % resultTable=probeTableCell{CSVIndex,1}
    % resultTable=tempRawTable;
    % resultTable=ResultTableFromCSVPerStudy
    varName='case Range';

%% `resultTable`에서 `varName` 열에서 'case range' 문자열을 검색합니다.
    caseRangeLineIdxList = find(contains(resultTable.(varName), 'case range','IgnoreCase',true));
    TablesCellCaseRowDataCol = table();      % 각 'case range' 구간을 찾고 해당 구간을 별도의 테이블로 분리합니다.
    %% mkRow - Case Number
    FistIdx     =caseRangeLineIdxList(1);          % Case Range Line
    caseLineIdx  =resultTable(FistIdx,:);
    CaseList     =removeEmptyCells(caseLineIdx.Variables);
    CaseList     =CaseList(2:end);
    CaseList     =cellfun(@(x) strrep(x,'"',''),CaseList,'UniformOutput',false);
    CaseList     =cellfun(@(x) str2double(x),CaseList,'UniformOutput',false);
    Numcases     =length(CaseList);
    for caseIndex=1:length(CaseList)
        TablesCellCaseRowDataCol(caseIndex,'Case')={caseIndex};
    end
    TablesCellCaseRowDataCol.Properties.RowNames=cellstr(num2str(TablesCellCaseRowDataCol.Case));
    TablesCellCaseRowDataCol=removevars(TablesCellCaseRowDataCol,"Case");
    TablesCellCaseRowDataCol.Properties.DimensionNames=[{'Case'} {'Variables'}];
    %% mkCol - DataSet or GraphName
    if ~(FistIdx==1)  % from DataSet
       DataSetNameIndexList    =caseRangeLineIdxList-1;
       DataSetNameList         =cell(length(DataSetNameIndexList),1);
       for DataNameIndex=1:length(DataSetNameIndexList)
           DataNameRowIndex=DataSetNameIndexList(DataNameIndex);
           if ~isEmptyCheck(resultTable(DataNameRowIndex,1).Variables)
            DataSetNameList(DataNameIndex,1)=resultTable(DataNameRowIndex,1).Variables;
           else
               NonEmptyVars=findEmptyVars(resultTable(DataNameRowIndex,:),1);
               DataSetNameList(DataNameIndex,1)=resultTable(DataNameRowIndex,NonEmptyVars).Variables;
           end
       end
       % DataSetNameList         =resultTable(DataSetNameIndexList,1).Variables;   
       DataSetNameList = cellfun(@(x) strrep(x, ' ', ''), DataSetNameList, 'UniformOutput', false);  
       DataSetNameList = cellfun(@(x) strrep(x, '<Value>', ''), DataSetNameList, 'UniformOutput', false);  
       NumDataSet      = length(DataSetNameList);       
       TablesCellCaseRowDataCol(:,DataSetNameList)=cell(Numcases,NumDataSet);
       endIndexShiftLine=-2;  %% DataName이 있음
       NumColoumn=NumDataSet;
    else  % From Direct Graph
       GraphNameIndexList= caseRangeLineIdxList+1;% Data Unit List
       GraphNameList      =resultTable(GraphNameIndexList,2).Variables;   
       GraphNameList = cellfun(@(x) strrep(x, ' ', ''), GraphNameList, 'UniformOutput', false);  
       GraphNameList = cellfun(@(x) strrep(x, '<Value>', ''), GraphNameList, 'UniformOutput', false);  
       NumGraphList  = length(GraphNameList);
       TablesCellCaseRowDataCol(:,GraphNameList)=cell(Numcases,NumGraphList);
       endIndexShiftLine=-1;  %% 데이터 네임은 없고 Graph Name만있음
       NumColoumn=NumGraphList;
    end  
 
    %% 데이터별로 테이블 쪼개기
    %% 각 'case range' 구간을 찾고 해당 구간을 별도의 테이블로 분리합니다.
    for ColIdx = 1:NumColoumn
        % 현재 'case range' 행의 인덱스
        curRow_containCaseRangeIdx = caseRangeLineIdxList(ColIdx) ;
        curDataStartRowIdx         = curRow_containCaseRangeIdx+2;  % 그래프이름이 무조건있으니까
        % GraphName별로 분리
        curDataGraphNameLineIndex             =curRow_containCaseRangeIdx+1;% Data Unit List
        % 다음 'case range' 행의 인덱스를 찾습니다.
        if ColIdx < width(TablesCellCaseRowDataCol)
            endIdx = caseRangeLineIdxList(ColIdx+1) + endIndexShiftLine;
        else
            endIdx = height(resultTable)+endIndexShiftLine+1; % 마지막 'case range' 이후로는 테이블의 마지막 행까지 선택
        end
   
        emptyVars = varfun(@(x) all(cellfun(@isempty, x)), resultTable(curDataGraphNameLineIndex,:) , 'OutputFormat', 'uniform');
        emptyVarIndices = find(emptyVars);   % 비어있는 변수의 인덱스 찾기
        if ~isempty(emptyVarIndices)
            % 연속적으로 비어있는 인덱스 중 첫 번째만 남기기
            diffIndices = [1, diff(emptyVarIndices)];         % 각 비어있는 인덱스 사이의 차이
            nonConsecutive = [true, diffIndices(2:end) > 1];  % 차이가 1보다 큰 경우만 유지
            emptyVarIndices = emptyVarIndices(nonConsecutive);
        end
        prevColIdx = 1;
        %% case-  비어있는 변수를 기준으로 테이블 쪼개기
        for caseIndex = 1:length(emptyVarIndices)
            curColIdx                  =emptyVarIndices(caseIndex);
            uniqueColNamesParts             =makeUniqueColNames(resultTable(curDataGraphNameLineIndex, prevColIdx:(curColIdx-1)).Variables);
            uniqueColNamesParts     =cellfun(@(x) strrep(x,'"',''),uniqueColNamesParts,'UniformOutput',false);
            GraphTableByCaseByData     =resultTable(curDataStartRowIdx:endIdx, prevColIdx:(curColIdx-1));        
            uniqueColNamesParts = matlab.lang.makeUniqueStrings(matlab.lang.makeValidName(uniqueColNamesParts), {}, namelengthmax);
            GraphTableByCaseByData.Properties.VariableNames      =uniqueColNamesParts;
            numericTable  = convertCharCellTable2Numeric(GraphTableByCaseByData); 
            if ~isempty(numericTable.Variables)&~any(all(isnan(numericTable.Variables)))
                 if any(contains(numericTable.Properties.VariableNames,'Freq','IgnoreCase',true))
                     numericTable  = convertNumTable2TFreqTable(numericTable);
                 elseif any(contains(numericTable.Properties.VariableNames,'time','IgnoreCase',true))
                     numericTable  = convertNumTable2TimeTable(numericTable);
                 end
            end
            TablesCellCaseRowDataCol(caseIndex,ColIdx) = {numericTable};
            prevColIdx = curColIdx + 1;
        end
    end
end

