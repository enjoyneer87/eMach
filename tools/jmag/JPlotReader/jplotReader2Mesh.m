

% [ElementId{SlotIndex}, NodeID{SlotIndex},NodeTable{SlotIndex},delaunyObj{SlotIndex}]...


slotElementIds=[];
slotNodeID=[];
for SlotIndex=1:1
    slotElementIds=[slotElementIds; ElementId{SlotIndex}];
    slotNodeID=[slotNodeID; NodeID{SlotIndex}];
end

% AllelementCentersTable 로부터 eleType별로 Mesh 만들기

slotNodeCoord   =[slotNodeID AllNodeTable.x(slotNodeID,:),AllNodeTable.y(slotNodeID,:)];

triSlotEleIdx  =ismember(AllelementCentersTable.id,slotElementIds)&AllelementCentersTable.eleType==2;
quadSlotEleIdx =ismember(AllelementCentersTable.id,slotElementIds)&AllelementCentersTable.eleType==3;

slottriElementCoord=[AllelementCentersTable.x(triSlotEleIdx,:),AllelementCentersTable.y(triSlotEleIdx,:)];
slotquadElementCoord=[AllelementCentersTable.x(quadSlotEleIdx,:),AllelementCentersTable.y(quadSlotEleIdx,:)];


updatedTri = filterDelaunayByIncenter(slotNodeCoord(:,[2,3]), slottriElementCoord);
triplot(updatedTri)
hold on
eleType=AllelementCentersTable.eleType
slotEleTypeList=eleType(slotElementIds,:);
EleTypeList=slotEleTypeList
% EleconnectList = findAdaptiveNearestNodesOptimized(slotquadElementCoord,slotNodeCoord,slotEleTypeList );

size(slotNodeCoord)

quadMesh = generateQuadMeshUsingVoronoi(slotNodeCoord(:,1),slotNodeCoord(:,2:3),slotquadElementCoord)
nearestQuadrilateralNodes      = findNearestNodes4quadMesh(slotNodeCoord(:,1),slotNodeCoord(:,2:3),slotquadElementCoord);

nearestNodes = findNearestNodes4quadMesh(nodeId, nodes, centerPoints, numNodes)
nearestQuadrilateralNodes      = findNearestNodes(slotNodeCoord(:,1),slotNodeCoord(:,2:3),slotquadElementCoord,4);
%%
patch('Faces', 1:numNodes, 'Vertices', nodes(quadNodes, :), 'FaceColor', 'cyan', 'EdgeColor', 'black');  % 마름모 또는 사각형 패치


x=dt.Points(:,1)
y=dt.Points(:,2)
boundaryEdges=freeBoundary(dt)
for idx=1:len(boundaryEdges)
plot(x(boundaryEdges(idx,:)),y(boundaryEdges(idx,:)),'LineWidth',2)
hold on
end
boundaryEdgesCoord=[x(boundaryEdges),y(boundaryEdges)]
hold off;
title('Delaunay Triangulation with Boundary Edges Highlighted');
axis equal;

quadMesh = generateQuadMesh(nodes, elementCenters, boundaryEdges)

scatter(nodes(:,1),nodes(:,2),'og')

C = linspecer(2*len(selectedNodeCoords));
selectedNodeCoords=[];
for eleIdx=1:len(quadMesh)
    if ~(quadMesh(eleIdx,:)==0)
    selectedNodeCoords=[selectedNodeCoords;[nodes(quadMesh(eleIdx,:)',1),nodes(quadMesh(eleIdx,:)',2)]];
    end
end
for eleIdx=1:4:len(selectedNodeCoords)

        % scatter(selectedNodeCoords(eleIdx:eleIdx+3,1),selectedNodeCoords(eleIdx:eleIdx+3,2),'*','filled','MarkerEdgeColor',C(2*eleIdx,:))
        plot(selectedNodeCoords(eleIdx:eleIdx+3,1),selectedNodeCoords(eleIdx:eleIdx+3,2))

        hold on
end
nodes(quadMesh,
elementCenters=slotquadElementCoord
plotQuadmesh(quadMesh,slotNodeCoord(:,2),slotNodeCoord(:,3))
nodes=[AllNodeTable.x,AllNodeTable.y]
for i = 1:numCenters
        % 각 요소의 4개의 노드 좌표 추출
        quadNodes = nearestNodes(i, :);  % 4개의 노드 인덱스
        patch('Faces', repmat(1:numNodes,numCenters,1), 'Vertices', nodes(nearestNodes, :), 'FaceColor', 'cyan', 'EdgeColor', 'black');  % 마름모 또는 사각형 패치
end


centerPoints=slotquadElementCoord
nodeId=slotNodeCoord(:,1)
nodesCoord=slotNodeCoord(:,2:3)
nearestNodes=nearestQuadrilateralNodes

plot(slotquadElementCoord(:,1),slotquadElementCoord(:,2),'*r')
hold on
plot(slotNodeCoord(:,2),slotNodeCoord(:,3),'ob')
scatter(slotquadElementCoord(2,1),slotquadElementCoord(2,2))
hold on

plotQuadmesh(nearestQuadrilateralNodes',AllNodeTable.x,AllNodeTable.y)

patch()


qudeNode        =slotNodeCoord(unique(nearestQuadrilateralNodes),:)
slotNodeCoord        =[[1:size(slotNodeCoord,1)]',slotNodeCoord]
% nodeIndex       = containers.Map(qudeNode(:,1), 1:size(qudeNode,1));
quadElements    =nearestQuadrilateralNodes

% pdeQuadElements = arrayfun(@(x) nodeIndex(x), quadElements(:, 1:4));
hh = plotQuadmesh(nearestQuadrilateralNodes', slotNodeCoord(:,2),slotNodeCoord(:,3))

 %%
plot(slotNodeCoord(nearestQuadrilateralNodes(1,:)',1),slotNodeCoord(nearestQuadrilateralNodes(1,:)',2))
%%
quadmesh(nearestQuadrilateralNodes',qudeNode(:,1),qudeNode(:,2))

nodeIndex = containers.Map(qudeNode(:,1), 1:size(qudeNode,1));
pdeTriElements = arrayfun(@(x) nodeIndex(x), triElements(:, 2:4));
pdeQuadElements = arrayfun(@(x) nodeIndex(x), quadElements(:, 1:4));

triConnect  = EleconnectList(slotEleTypeList==2);
triMat      =cell2mat(triConnect);
triT        =triangulation(triMat,[AllNodeTable.x,AllNodeTable.y]);
triplot(triT);

voronoi(nearestQuadrilateralNodes(:,1),nearestQuadrilateralNodes(:,2))
plotQuadMesh(slotNodeCoord, nearestQuadrilateralNodes)
triDT=delaunayTriangulation(slotNodeCoord)
triplot(triDT)

% Idx2 = knnsearch(X,Y,Distance="fasteuclidean",CacheSize=100); % Warm up function

eleType=AllelementCentersTable.eleType;


%% quadMesh
quadConnect= EleconnectList(slotEleTypeList==3)
quadMat=cell2mat(quadConnect)
quadElements=[slotElementIds(slotEleTypeList==3) quadMat]

%5 quadMesh
quadNodesID=[quadConnect{:}];
qudNodesID=unique(quadNodesID);
quadNodes=slotNodeCoord(quadNodesID,:);


patch('Faces', quadMat, 'Vertices', quadNodes, 'FaceColor', 'cyan');
quadmesh(quadMat,quadNodes(:,1),quadNodes(:,2))

%% TriMesh
triConnect= EleconnectList(slotEleTypeList==2);
triMat=cell2mat(triConnect);

triNodesID=[triConnect{:}];
triNodesID=unique(triNodesID);
trinodes=slotNodeCoord(triNodesID,:);
%%plot Tri
% triT=triangulation(triMat,trinodes)
triDT=delaunayTriangulation(trinodes)
triplot(triDT)


%%
%5
% nodes = sortrows(nodes, 1);
triElements = sortrows(triElements, 1);
quadElements = sortrows(quadElements, 1);

% 노드 ID를 인덱스로 변환
nodeIndex = containers.Map(nodes(:,1), 1:size(nodes,1));
pdeTriElements = arrayfun(@(x) nodeIndex(x), triElements(:, 2:4));
pdeQuadElements = arrayfun(@(x) nodeIndex(x), quadElements(:, 2:5));

 hh = plotQuadmesh(quadElements, nodes(:,1), nodes(:,2));

 quadElements(:,1)=[1:height(quadElements)]'
 size(quadElements)



 %%
 % 예시 입력 데이터 (사용자가 제공한 실제 데이터로 교체 가능)
nodeId = (1:8)';  % 노드 ID
nodes = [0 0; 1 0; 1 1; 0 1; 0 0.5; 0.5 1; 1 0.5; 0.5 0];  % 노드 좌표
centerPoints = [0.5 0.5];  % 중심점 좌표
numNodes = 4;  % 가장 가까운 노드 4개 찾기


% 패치 그리기
figure;
hold on;

scatter(nodes(:,1),nodes(:,2))
% 가장 가까운 노드 찾기
nearestNodes = findNearestNodes(nodeId, nodes, centerPoints, numNodes);

% 각 요소에 대해 패치 그리기
for i = 1:size(nearestQuadrilateralNodes, 1)
    % nearestNodes에 해당하는 노드의 좌표
    patchCoords = nodes(nearestQuadrilateralNodes(i, :), :);
    
    % 패치 그리기 (시계 방향으로 연결된 노드 좌표)
    patch('Vertices', nodes, 'Faces', nearestQuadrilateralNodes(i, :), ...
          'FaceColor', 'cyan', 'EdgeColor', 'black');
end

plot(quadnodes(:,1),quadnodes(:,2),'ob')
hold on
plot(slotquadElementCoord(:,1),slotquadElementCoord(:,2),'*r')

quadnodes=[]
for i = 1:numCenters
quadnodes=[quadnodes;nodes(nearestQuadrilateralNodes(i,:), :)];
end
        patch('Faces', 1:4, 'Vertices', quadnodes(6:9,:), 'FaceColor', 'cyan', 'EdgeColor', 'black');  % 마름모 또는 사각형 패치


for i = 1:numCenters
        % 각 요소의 4개의 노드 좌표 추출
        patch('Faces', reshape(1:len(nearestQuadrilateralNodes)*4,4,numCenters)', 'Vertices', quadnodes, 'FaceColor', 'cyan', 'EdgeColor', 'black');  % 마름모 또는 사각형 패치
end
% 보기 좋게 시각화
axis equal;
xlabel('X');
ylabel('Y');
title('Quad Mesh using nearestNodes');
hold off;