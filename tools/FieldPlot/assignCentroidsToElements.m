function combinedElementsWithCentroids = assignCentroidsToElements(combinedElements, pdeNodes)
    % assignCentroidsToElements - 각 요소의 중앙 위치 좌표를 계산하여 구조체에 추가
    %
    % combinedElements: 구조체로, 각 파트별로 요소 ID 및 연결 노드 정보가 포함
    % pdenodes: 3 x N 배열로, 노드 번호별 X, Y, Z 좌표가 포함
    %
    % combinedElementsWithCentroids: 각 요소에 중앙 좌표가 추가된 구조체

    combinedElementsWithCentroids = combinedElements;  % 결과 구조체 초기화

    % 파트별 필드 이름(파트 ID) 가져오기
    partFields = fieldnames(combinedElements);
    
    % 파트별로 요소들의 중심 좌표를 계산
    for i = 1:length(partFields)
        partID = partFields{i};
        elements = combinedElements.(partID);  % 해당 파트의 요소들
        numElements = size(elements, 1);
        
        % 각 요소의 중심 좌표 계산
        centroids = zeros(numElements, 3);  % 중심 좌표를 저장할 배열

        for j = 1:numElements

            elementNodeIDs = elements(j, 2:end);  % 요소의 연결 노드 IDs
            elementNodeIDs = elementNodeIDs(~isnan(elementNodeIDs));
            elementNodeCoords = pdeNodes(:,elementNodeIDs);  % 노드 좌표 추출
            centroids(j, :) = calcCentroid(elementNodeCoords');  % 중심 좌표 계산
        end
        
        % 계산된 중심 좌표를 요소 정보 옆에 추가
        combinedElementsWithCentroids.(partID) = [combinedElements.(partID), centroids];
    end
end