function dataSetTable=getJMagDataSet2MLabTable(DataObj)

%% DataSet Class
% DataObj=DataSet{DataSetIndex}

%% 행렬  - JMAG DataSet- MatTable간 행렬 바뀜 주의
NumCols=DataObj.GetCols(); % JMAG 기준 (DataName)
NumRows=DataObj.GetRows(); % JMAG 기준 (Step)

%% DataName Cell
% clear DataName
ColIndex=1;
DataName{ColIndex}=DataObj.GetXAxisTitle;
for ColIndex=2:NumCols
DataName{ColIndex}=DataObj.GetColumnName(ColIndex-1);
end

% 중복 이름에 숫자 추가 (Flux Linkage 처럼 여러개일때)
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

% for RowIndex=1:NumRows
% StepNames{RowIndex}=DataObj.GetRange(RowIndex-1);
% end

%% MatLab 테이블 생성
initialData = zeros(NumRows, NumCols);

% 빈 테이블 생성
% dataTable = array2table(initialData, 'VariableNames', uniqueNames, 'RowNames', StepNames);
dataSetTable = array2table(initialData, 'VariableNames', uniqueNames);

unititleCol=find(contains(uniqueNames,'untitle'), 1);
if ~isempty(unititleCol)
    uniqueNames{unititleCol}=DataObj.GetYAxisTitle;
end
%% 테이블에 데이터 입력
for StepIndex=1:NumRows
    for VariableIndex=1:NumCols
    dataSetTable{StepIndex,VariableIndex}= DataObj.GetValue(StepIndex-1,VariableIndex-1);
    end
end

dataSetTable.Properties.VariableUnits=[{DataObj.GetXAxisTitle},repmat({DataObj.GetYAxisUnit},1,NumCols-1)];
dataSetTable.Properties.Description=DataObj.GetName;

%% TB

% StepNames{RowIndex}=DataObj.GetTimeUnit();
% DataObj.GetAngle(1)
% DataObj.GetTime(1)
% DataObj.GetComponent
% dataTable.Properties.VariableUnits=DataObj.GetValueUnit()
% dataTable.Properties.DimensionNames={'Step',''}
end