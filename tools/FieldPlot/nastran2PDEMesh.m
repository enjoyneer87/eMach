function [model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(csvFile)
    % csvFile: 메쉬 데이터가 포함된 CSV 파일 경로
    % csvFile=MPToolCSVFilePath
    % CSV 파일 읽기
    data = readtable(csvFile, 'Delimiter', ',', 'ReadVariableNames', false);

    % GRID, CTRIA3, CQUAD4 데이터를 필터링
    gridData   = data(contains(data.Var1, 'GRID'), :);
    ctria3Data = data(contains(data.Var1, 'CTRIA3'), :);
    cquad4Data = data(contains(data.Var1, 'CQUAD4'), :);
    
    %% Grid 
    % 	GRID: 카드의 이름을 나타냅니다.
	% •	ID: 노드 ID를 나타냅니다.
	% •	CP: 정의된 좌표계의 ID를 나타냅니다.
	% •	X1, X2, X3: 노드의 위치 좌표를 나타냅니다.
	% •	CD: 해석에서 사용하는 출력 좌표계의 ID를 나타냅니다.
	% •	PS: 기본 변위를 나타내는 스칼라 또는 벡터 포인트를 나타냅니다.
	% •	SEID: 최상위 모델의 대체 좌표 시스템에서의 속성입니다.

    %% CTRIA3
 	% CTRIA3: 카드의 이름을 나타냅니다.
	% •	EID: 요소 ID를 나타냅니다.
	% •	PID: 속성 ID (Property ID)를 나타냅니다.
	% •	G1, G2, G3: 삼각형 요소를 구성하는 세 노드의 ID를 나타냅니다.
    
    %% CQUAD4
	% •	CQUAD4: 카드의 이름을 나타냅니다.
	% •	EID: 요소 ID를 나타냅니다.
	% •	PID: 속성 ID (Property ID)를 나타냅니다. -      %PSHELL, PCOMP 또는 PPLANE 정의
	% •	G1, G2, G3, G4: 사각형 요소를 구성하는 네 노드의 ID를 나타냅니다.

    %% PShell
    % •	PID: 속성 ID
	% •	MID1: 첫 번째 물질 ID
	% •	T: 요소 두께           
	% •	MID2: 두 번째 물질 ID (재료 변경 시 사용)
	% •	12I/T3: 전단 수정 계수
	% •	MID3: 세 번째 물질 ID (재료 변경 시 사용)
	% •	TS/T: 비틀림 계수
	% •	NSM: 비구조물 질량

    %% Parsing
    % GRID 데이터 파싱
    nodeIDs              = gridData.Var2;
    coords               = gridData(:, 4:6);
    coords               = table2array(coords);
    nodes                = [nodeIDs, m2mm(coords)];

    % CTRIA3 데이터 파싱
    triElementIDs       = ctria3Data.Var2;
    CTRIA3PID           = ctria3Data.Var3;
    triNodes            = ctria3Data(:, 4:6);
    triNodes            = table2array(triNodes);
    triElements         = [triElementIDs, triNodes];

    % CQUAD4 데이터 파싱
    quadElementIDs      = cquad4Data.Var2;
    CQUAD4PID           = cquad4Data.Var3;
    quadNodes           = cquad4Data(:, 4:7);
    quadNodes           = table2array(quadNodes);
    quadElements        = [quadElementIDs, quadNodes];

    % 노드와 요소 ID로 정렬
    nodes               = sortrows(nodes, 1);
    triElements         = sortrows(triElements, 1);
    quadElements        = sortrows(quadElements, 1);

   % 노드 ID 인덱스를 생성하여 누락된 노드를 추가
    nodeIndexMap = containers.Map(nodes(:,1), 1:size(nodes,1));
    maxNodeID = max(nodeIDs);
    missingNodeIDs = setdiff(1:maxNodeID, nodes(:, 1));
    
    % 누락된 노드를 기본 좌표 (0, 0, 0)로 추가
    for i = 1:length(missingNodeIDs)
        nodes = [nodes; missingNodeIDs(i), 0, 0, 0];
    end
    
    % 노드와 요소 ID로 다시 정렬
    nodes = sortrows(nodes, 1);
    triElements = sortrows(triElements, 1);
    quadElements = sortrows(quadElements, 1);

    % 노드 ID를 인덱스로 변환
    nodeIndex = containers.Map(nodes(:,1), 1:size(nodes,1));
    pdeTriElements = arrayfun(@(x) nodeIndex(x), triElements(:, 2:4));
    pdeQuadElements = arrayfun(@(x) nodeIndex(x), quadElements(:, 2:5));

    % 배열을 전치하여 형식을 맞춤
    pdeTriElements = pdeTriElements';
    pdeQuadElements = pdeQuadElements';

    % 삼각형 요소에 네 번째 행을 추가하여 0으로 채움
    % pdeTriElements(4, :) = 0;

    % 삼각형과 사각형 요소를 결합하여 하나의 요소 배열로 만듦
    pdeElements = [pdeTriElements];

    % 노드 좌표 설정
    pdeNodes = nodes(:, 2:4)';

    pdeNodes(3, :) = 0;

    % PDE 모델 생성 및 메쉬 추가
    
    model = createpde();
    geometryFromMesh(model, pdeNodes(1:2,:), pdeTriElements(1:3,:));

    %% 3D Plot

    % % 3차원 PDE 모델 생성
    % model = createpde(3);
    % 
    % % 3차원 메쉬의 노드와 요소를 정의
    % % pdeNodes는 3xN 행렬, pdeTriElements는 4xM 행렬
    % % pdeNodes: 3xN 행렬 (x, y, z 좌표)
    % % pdeTriElements: 4xM 행렬 (4개의 노드 인덱스, 테트라헤드럴 요소)
    % 
    % geometryFromMesh(model, pdeNodes(1:3,:), pdeTriElements(1:4,:));
    
    % % 플롯 설정
    % pdegplot(model, 'FaceLabels', 'on', 'FaceAlpha', 0.5);
    % axis equal;
    % view(3);

end