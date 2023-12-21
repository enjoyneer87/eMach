function resultTable=getCoilNumberTablePerSlotLayer(TargetTable,SlotType)
% TargetTable은 MCADTable로부터  정리

T=TargetTable; % Phase per Parallel Number
% T=NewWindingTable

if strcmp(SlotType,'GoSlot')
    RadialPositionName='GoRadialPosition';
elseif strcmp(SlotType,'ReturnSlot')
    RadialPositionName='ReturnRadialPosition';
end
% 결과 테이블을 초기화합니다.
resultTable = table();

% 모든 고유한 GoSlot 값에 대해 반복합니다.
% uniqueGoSlots = unique(T.ValueTable(strcmp(T.TypeofData, 'GoSlot')));
uniqueGoSlots = unique(T.ValueTable(strcmp(T.TypeofData, SlotType)));

% 각 GoSlot 값에 대한 CoilNumbers와 매칭되는 GoRadialPosition을 찾습니다.
for i = 1:length(uniqueGoSlots)
    % 현재 GoSlot 값
    currentGoSlot = uniqueGoSlots{i};
    
    % 현재 GoSlot에 해당하는 CoilNumber 추출
    goSlotCoilNumbers = T.CoilNumber(strcmp(T.TypeofData, SlotType) & strcmp(T.ValueTable, currentGoSlot));
    
    % 같은 CoilNumber를 가지고 있는 GoRadialPosition의 ValueTable 값 추출
    goRadialPositionLayers = T.ValueTable(strcmp(T.TypeofData, RadialPositionName) & ismember(T.CoilNumber, goSlotCoilNumbers));
    
    % 이제 goRadialPositionLayers를 Layer 번호로 사용하여 resultTable을 채웁니다.
    % 여기서는 각 Layer 번호를 행으로, GoSlot 값을 열로 사용합니다.
    for j = 1:length(goRadialPositionLayers)
        layerNumber = str2double(goRadialPositionLayers{j}); % Layer 번호를 추출 (문자열을 숫자로 변환)
        
        % 결과 테이블에 현재 슬롯의 Layer 번호와 코일 번호를 저장합니다.
        resultTable.(sprintf('Slot%s', currentGoSlot))(layerNumber, 1) = goSlotCoilNumbers(j);
    end
end

% 각 변수명(슬롯 번호)에서 숫자 추출
variableNames = resultTable.Properties.VariableNames;
slotNumbers = cellfun(@(x) str2double(regexp(x, '\d+', 'match')), variableNames);

% 숫자를 기준으로 정렬하여 인덱스를 가져옵니다.
[~, sortedIndices] = sort(slotNumbers);

% 테이블의 변수들을 정렬된 순서로 재배치합니다.
resultTable = resultTable(:, sortedIndices);


% 각 변수명(슬롯 번호)에서 숫자 추출
variableNames = resultTable.Properties.VariableNames;
slotNumbers = cellfun(@(x) str2double(regexp(x, '\d+', 'match')), variableNames);

% 숫자를 기준으로 정렬하여 인덱스를 가져옵니다.
[~, sortedIndices] = sort(slotNumbers);

% 테이블의 변수들을 정렬된 순서로 재배치합니다.
resultTable = resultTable(:, sortedIndices);


%%
% 'GoRadialPosition' 값들을 순차적으로 정렬합니다.
[sortedGoRadialPositions, goRadialOrder] = sort(goRadialPositionLayers);

% 행 이름을 설정합니다.
rowNames = strcat('Layer', cellstr((sortedGoRadialPositions)));
% resultTable.Properties.RowNames = rowNames;

end
% 결과 테이블의 변수 확인
