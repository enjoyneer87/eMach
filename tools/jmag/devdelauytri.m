%% delaunayTriangulation
centerAllFigures
 DT = delaunayTriangulation(updatedElements);


nodesPos=PartStruct(slotIndex).NodeTable.nodeCoords
elements =PartStruct(slotIndex).connetivity.elementConnectivity

% 1. 노드 번호가 1부터 시작하지 않는 경우를 처리
uniqueNodeIDs = unique(elements(:));   % 사용된 모든 노드 번호 추출
numNodes = length(uniqueNodeIDs);      % 고유 노드의 수
newIndexMap = zeros(max(uniqueNodeIDs), 1); % 노드 번호 -> 새로운 인덱스로 매핑

% 2. 노드 번호를 1번부터 시작하도록 매핑
newIndexMap(uniqueNodeIDs) = 1:numNodes;

% 3. 요소의 노드 번호를 새로운 인덱스로 업데이트
updatedElements = arrayfun(@(x) newIndexMap(x), elements);

% 4. 새로운 인덱스에 따라 노드 좌표 재정렬
updatedNodes = nodesPos;
DT = triangulation(reshape(cell2mat(updatedElements),len(elements),3),updatedNodes);

% 5. delaunayTriangulation 객체 생성
zData=PartStruct(slotIndex).fieldxTimeTable

for slotIndex=1:len(PartStruct)
        % BData=WireTable(slotIndex,:);
        % triangulate(BData.NodeTable.nodeCoords)     
        % DT = delaunayTriangulation(BData.NodeTable.nodeCoords)
        DT = triangulation(updatedElements,updatedNodes);

        DT.Points=BData.NodeTable.nodeCoords
        DT.ConnectivityList=PartStruct(slotIndex).connetivity.elementConnectivity
        IC = incenter(DT);
        triplot(DT)
        hold on
        plot(IC(:,1),IC(:,2),'*r')
        % scatter3(m2mm(BData.elementCentersTable{:}(:,'x').Variables),m2mm(BData.elementCentersTable{:}(:,'y').Variables),BData.fieldxTimeTable{:}(timeList(timeindex),:).Variables,'MarkerEdgeColor',timeColorList{timeindex},'MarkerFaceColor','none','Marker',SlotList{slotIndex})
        hold on
end
trisurf(K,DT.Points(:,1),DT.Points(:,2),DT.Points(:,3))


for slotIndex = 1:len(PartStruct)
    BData = WireTable(slotIndex, :);
    
    % Delaunay 삼각화 생성
    DT = delaunayTriangulation(BData.NodeTable.nodeCoords);
    
    % 각 삼각형 요소의 중심점 계산
    IC = incenter(DT);
    
    % 요소 중심에 대응하는 z 데이터 (예시: 임의의 z 데이터, 실제 데이터로 교체)
    zData = BData.fieldxTimeTable(1, :).Variables; % 요소 중심 z 데이터
    
    % 각 삼각형의 좌표와 zData를 기반으로 patch 생성
    tris = DT.ConnectivityList; % 삼각형의 노드 인덱스
    
    % 삼각형 중심에 zData를 할당하여 시각화
    patch('Faces', tris, 'Vertices', [IC, zData'], ...
          'FaceVertexCData', zData', 'FaceColor', 'flat', 'EdgeColor', 'none');
  
    hold on;
    
    % 삼각형 요소 경계선 표시 (원하는 경우)
    triplot(DT, BData.NodeTable.nodeCoords(:,1), BData.NodeTable.nodeCoords(:,2), 'k');
    
    % 요소 중심점 표시
    plot(IC(:,1), IC(:,2), '*r');
    
    hold on;
end

% 3D 뷰 설정
view(3);
colorbar;



close all
triplot(DT)
hold on
scatter3(IC(:,1),IC(:,2),Fr(1,:))

scatter3(IC(:,1),IC(:,2),Ftheta(2,:))

centerAllFigures    