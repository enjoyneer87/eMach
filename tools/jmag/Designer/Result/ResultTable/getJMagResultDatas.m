function ResultDataStruct = getJMagResultDatas(LossStudyResultTableObj, varargin)
    % 선택적 인자 처리
    if ~isempty(varargin)
        targetString = varargin{1};
    else
        targetString = '';
    end
    
    NumTables = LossStudyResultTableObj.NumTables;

    % 결과를 저장할 구조체 배열 초기화
    ResultDataStruct = struct('DataObj', {}, 'DataName', {}, 'dataTable', {});
    
    for TableIndex = 1:NumTables
        if LossStudyResultTableObj.GetData(TableIndex-1).IsValid
            % 임시 변수에 DataObj 저장
            tempDataObj = LossStudyResultTableObj.GetData(TableIndex-1);
            
            % 문자열이 주어진 경우 해당 문자열 포함 여부 확인
            if ~isempty(targetString)
                if contains(tempDataObj.GetName, targetString, 'IgnoreCase', true)
                    % 조건을 만족하면 정보 저장
                    ResultDataStruct(end+1).DataObj = tempDataObj;
                    ResultDataStruct(end).DataName = tempDataObj.GetName;
                    ResultDataStruct(end).DataUnit = extractAfter(ResultDataStruct(end).DataName,':');
                    ResultDataStruct(end).dataTable = getJMagResultData2MLabTable(tempDataObj);
                end
            else
                % 문자열이 주어지지 않은 경우 모든 데이터 저장
                ResultDataStruct(end+1).DataObj = tempDataObj;
                ResultDataStruct(end).DataName = tempDataObj.GetName;
                ResultDataStruct(end).dataTable = getJMagResultData2MLabTable(tempDataObj);
                
            end
        end
    end

    % 비어있는 행 삭제
    % 비어있는 'DataObj' 필드를 기준으로 비어있는 행을 찾아 제거
    nonEmptyIndices = ~arrayfun(@(x) isempty(x.DataObj), ResultDataStruct);
    ResultDataStruct = ResultDataStruct(nonEmptyIndices);
end
