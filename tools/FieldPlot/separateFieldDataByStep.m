function FieldDataSteps = separateFieldDataByStep(FieldData, FieldKeyIndex,startStep)
    if nargin<3
    startStep=1;
    end
    numSteps = length(FieldKeyIndex);
    FieldDataSteps = cell(numSteps, 1);

    % 각 스텝별로 데이터를 처리
    for stepIdx = startStep:numSteps
        % 각 스텝의 시작과 끝 인덱스를 찾음
        startIdx = FieldKeyIndex(stepIdx) + 3;  % 데이터 시작 행 (3행 뒤)
        if stepIdx < numSteps
            endIdx = FieldKeyIndex(stepIdx + 1) - 1;  % 다음 스텝 전까지
        else
            endIdx = height(FieldData);  % 마지막 스텝일 경우 끝까지
        end

        % 해당 범위의 데이터 추출
        FieldDataSteps{stepIdx} = FieldData(startIdx:endIdx, :);
        
        % 첫 번째, 두 번째, 세 번째 행 정보 추출
        postKeyIDRow = FieldData.Var1(FieldKeyIndex(stepIdx));
        stepNumberRow = FieldData.Var1(FieldKeyIndex(stepIdx) + 1);
        stepRow = FieldData.Var2(FieldKeyIndex(stepIdx) + 1);
        outputTypeRow = FieldData.Var3(FieldKeyIndex(stepIdx) + 1);
        physicalQuantityRow = FieldData.Var4(FieldKeyIndex(stepIdx) + 1);
        valueTypeRow = FieldData.Var5(FieldKeyIndex(stepIdx) + 1);
        elementOrNodeCount = FieldData.Var1(FieldKeyIndex(stepIdx) + 2);

        % 요소 또는 노드에 따른 변수 이름 설정
        if outputTypeRow==1  % 노드
            elementType = 'NodeID';
        elseif outputTypeRow==4  % 요소
            elementType = 'ElementID';
        end
 % 할당하려는 변수 길이에 따라 변수 삭제
        maxCols = 5; % 스칼라의 경우 예시
        switch physicalQuantityRow
            case 0  % 스칼라
                maxCols = 6; % 스칼라의 경우 6개의 컬럼이 있어야 함
            case 1  % 벡터
                maxCols = 10; % 벡터의 경우 10개의 컬럼이 있어야 함
            case 2  % 텐서
                maxCols = 16; % 텐서의 경우 16개의 컬럼이 있어야 함
        end


        % 할당할 변수 개수를 초과하는 열 삭제
        if width(FieldDataSteps{stepIdx}) > maxCols
            FieldDataSteps{stepIdx}(:, maxCols+1:end) = [];
        end
        % 물리량 유형 및 값 유형에 따른 변수 이름 설정
        switch physicalQuantityRow
            case 0  % 스칼라
                FieldDataSteps{stepIdx}.Properties.VariableNames = {elementType, 'X', 'Y', 'Z', 'ScalarValue', 'ImaginaryScalarValue'};
            case 1 % 벡터
                FieldDataSteps{stepIdx}.Properties.VariableNames = {elementType, 'X', 'Y', 'Z', 'VectorX', 'VectorY', 'VectorZ', 'ImagVectorX', 'ImagVectorY', 'ImagVectorZ'};
            case 2  % 텐서
                FieldDataSteps{stepIdx}.Properties.VariableNames = {elementType, 'X', 'Y', 'Z', 'TensorXX', 'TensorYY', 'TensorZZ', 'TensorXY', 'TensorYZ', 'TensorZX', 'ImagTensorXX', 'ImagTensorYY', 'ImagTensorZZ', 'ImagTensorXY', 'ImagTensorYZ', 'ImagTensorZX'};
        end
    end
    FieldDataSteps=removeEmptyCells(FieldDataSteps);
end