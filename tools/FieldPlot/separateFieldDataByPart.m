function partSeparatedData = separateFieldDataByPart(FieldDataSteps, combinedElements,selectPartIds)
    % FieldDataSteps: 각 스텝별로 테이블이 담긴 셀 배열
    % combinedElements: 파트별 요소 정보를 담은 구조체

    partFields = fieldnames(combinedElements);


    matchingPartIndexArray=findMatchingRow(partFields,selectPartIds);
    partSeparatedData = struct();

    % 각 스텝에 대해 반복 처리
    for stepIdx = 1:height(FieldDataSteps)
        currentStepData = FieldDataSteps{stepIdx}; % 현재 스텝의 테이블

        % 각 파트별로 데이터를 분리
        for partIndex = 1:length(matchingPartIndexArray)
            partName = partFields{matchingPartIndexArray(partIndex)};
            elementIDs = combinedElements.(partName)(:, 1); % 각 파트의 요소 ID 추출
        
            % 요소 ID로 필터링하여 각 파트에 맞는 데이터 추출
            partData = currentStepData(ismember(currentStepData.ElementID, num2str(elementIDs)), :);
            
            % 스텝별로 파트 데이터 저장
            if ~isfield(partSeparatedData, partName)
                partSeparatedData.(partName) = {};
            end
            partSeparatedData.(partName){stepIdx} = partData;
        end
    end
end