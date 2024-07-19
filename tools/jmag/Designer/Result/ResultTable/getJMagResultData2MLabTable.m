function dataTable=getJMagResultData2MLabTable(DataObj)

% MLAB == MatLAB
%% ResultTableData Class
% DataObj=ResultDataStruct(TableIndex).DataObj

%% 행렬  - JMAG Table과 MatTable간 행렬 바뀜 주의
NumCols=DataObj.GetCols(); % JMAG 기준 (DataName)
NumRows=DataObj.GetRows(); % JMAG 기준 (Step)

%% Unit 
DataUnit =extractAfter(DataObj.GetName,':');  %%??? 안나오는데

%% DataName Cell

for ColIndex=1:NumCols
DataName{ColIndex}=DataObj.GetColName(ColIndex-1);
end

% 중복 이름에 숫자 추가
uniqueNames = {}; % 고유 이름을 저장할 셀 배열 초기화
for i = 1:length(DataName)
    currentName = DataName{i};
    if sum(strcmp(uniqueNames, currentName)) == 0
        % 고유 이름이면 그대로 추가
        uniqueNames{end+1} = currentName; 
    else
        % 이름이 중복되면, 중복 횟수를 찾아 숫자를 추가
        count = sum(strcmp(DataName(1:i), currentName));
        newName = [currentName, num2str(count)];
        while sum(strcmp(uniqueNames, newName)) > 0
            % 이미 새 이름도 중복된 경우 숫자 증가
            count = count + 1;
            newName = [currentName, num2str(count)];
        end
        uniqueNames{end+1} = newName;
    end
end

%% StepName Cell
for RowIndex=1:NumRows
StepNames{RowIndex}=DataObj.GetRowName(RowIndex-1);
end

%% MatLab 테이블 생성
initialData = zeros(NumRows, NumCols);

% 빈 테이블 생성
dataTable = array2table(initialData, 'VariableNames', uniqueNames, 'RowNames', StepNames);


%% 테이블에 데이터 입력
for StepIndex=1:NumRows
    for VariableIndex=1:NumCols
    dataTable{StepIndex,VariableIndex}= DataObj.GetValue(StepIndex-1,VariableIndex-1);
    end
end

%% 단위
numVariables = width(dataTable); % 테이블의 변수(열) 수
dataTable.Properties.VariableUnits = repmat({DataUnit}, 1, numVariables);

%% TB

% StepNames{RowIndex}=DataObj.GetTimeUnit();
% DataObj.GetAngle(1)
% DataObj.GetTime(1)
% DataObj.GetComponent
% dataTable.Properties.DimensionNames={'Step',''}
end