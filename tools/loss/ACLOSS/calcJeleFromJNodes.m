function JeleTimeTable = calcJeleFromJNodes(elementCentersTable, JnodeTable)
    %
    % elementConnectivity=Slot1NodeConnectivity
    % JnodeTable=J0_fTable
    % 입력:
    %   meshNodes - 노드의 좌표 (Nx2 또는 Nx3 행렬, N은 노드 수)
    %   elementConnectivity - 요소를 정의하는 노드 연결 (MxK 행렬, M은 요소 수, K는 노드 수)
    %   nodeCurrentDensity - 노드별 전류 밀도 값 (Nx1 벡터, N은 노드 수)
    %
    % 출력:
    %   elementCurrentDensity - 요소별 전류 밀도 값 (Mx1 벡터, M은 요소 수)
    %
    % 예:
    %   elementCurrentDensity = calculateElementCurrentDensityFromNodes(meshNodes, elementConnectivity, nodeCurrentDensity);
    
    elementConnectivity  =elementCentersTable.elementConnectivity;
    numElements          = size(elementConnectivity, 1);  % 요소 수
    [timeSteps,~] =size(JnodeTable);
    elementCurrentDensity = zeros(timeSteps,numElements);  % 요소별 전류 밀도를 저장할 배열
    NodeIDs=cellfun(@(x) str2num(x), JnodeTable.Properties.VariableNames,'UniformOutput',false);
    NodeIDs=cell2mat(NodeIDs)';
    % 각 요소에 대해 해당 요소에 속하는 노드의 전류 밀도를 평균내서 계산
    for eleIndex = 1:numElements
        elementNodes = elementConnectivity(eleIndex, :);  % 요소의 노드 인덱스
        matchingIndices=findMatchingRow(NodeIDs,elementNodes);
        elementNodeDensities = JnodeTable(:,matchingIndices).Variables;  % 해당 요소 노드의 전류 밀도
        elementCurrentDensity(:,eleIndex) = mean(elementNodeDensities,2);  % 요소별 전류 밀도는 노드의 전류 밀도의 평균값
    end
    JeleTimeTable                          =array2table(elementCurrentDensity);
    JeleTimeTable.Properties.VariableNames =cellstr(num2str(elementCentersTable.id));
    JeleTimeTable.Properties.DimensionNames={'TimeStep','ElementID'};      
end