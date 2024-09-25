function combinedElements = combineElements(classifiedTriElements, classifiedQuadElements)
    % 두 구조체의 필드 이름을 가져옴
    triFields = fieldnames(classifiedTriElements);
    quadFields = fieldnames(classifiedQuadElements);

    % 새로운 구조체 생성
    combinedElements = struct();

    % classifiedTriElements의 필드를 추가
    for i = 1:length(triFields)
        combinedElements.(triFields{i}) = classifiedTriElements.(triFields{i});
    end

    % classifiedQuadElements의 필드를 추가
    for i = 1:length(quadFields)
        if isfield(combinedElements, quadFields{i})
            % 동일한 필드가 있으면 차원을 맞추기 위해 패딩 후 데이터 추가
            triData = combinedElements.(quadFields{i});
            quadData = classifiedQuadElements.(quadFields{i});
            
            % 두 배열의 열 수가 다를 경우, 작은 쪽을 NaN으로 패딩
            if size(triData, 2) < size(quadData, 2)
                triData(:, end+1:size(quadData, 2)) = NaN;
            elseif size(triData, 2) > size(quadData, 2)
                quadData(:, end+1:size(triData, 2)) = NaN;
            end
            
            % 데이터를 아래로 결합
            combinedElements.(quadFields{i}) = [triData; quadData];
        else
            % 새로운 필드면 그대로 추가
            combinedElements.(quadFields{i}) = classifiedQuadElements.(quadFields{i});
        end
    end
end