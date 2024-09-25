% Update Node
for slotIndex = 1:4
    nodesPos = WireTable.NodeTable(slotIndex).nodeCoords;  % 노드 좌표 가져오기
    elements = WireTable.connetivity{slotIndex}.elementConnectivity;  % 요소 연결성 가져오기
    DT{slotIndex}=createDelaunayTriangulation(elements,nodesPos);
end
%% calc HYB Eddy From B
close all
SlotFigIndex=[2*ones(1,4),3*ones(1,4),4*ones(1,4),5*ones(1,4),6*ones(1,4),7*ones(1,4)]
for slotIndex=1:24
    BData=table2struct(WireTable(slotIndex,:));
    xVar=BData.fieldxTimeTable.Variables
    yVar=BData.fieldyTimeTable.Variables
    xPos=BData.elementCentersTable.x'
    yPos=BData.elementCentersTable.y'
    [Fr,Ftheta]=cart2PolVector(xVar,yVar,xPos,yPos)
    Bfield(slotIndex).Br         = Fr     
    Bfield(slotIndex).Bthetam    = Ftheta   
    
    refDim=[0.2 0.1 150]
    speed =18000
    pole=8
    freqE= rpm2freqE(speed,pole/2);
    d=3.8
    w=7.2
    h=150
    [P1DG1P,P1DG2P,P2DG1P,P2DG2P,P2DG1,P2DG2,PrectP]  = calcHybridACLossWave('rectangular', refDim, rpm2freqE(speed,pole/2),Bfield);
    % P_loss = calcFatamiEddyCurrentLoss(Bfield, d, w, h, freqE)
end
%% Plot HYB P
figure(1)
for timeindex=1:1:len(timeList)
    for timeindex=1
    
        scatter3(xPos,yPos,P2DG2(timeList(timeindex),:)*10e4,'MarkerEdgeColor',timeColorList{timeindex},'MarkerFaceColor','none','DisplayName',num2str(3*timeList(timeindex)-3))
        hold on
    end

    TimeTotalLoss=sum(P2DG2,2)
    mean(TimeTotalLoss)*48
    figure(SlotFigIndex(slotIndex))
    
    plot(P2DG2)
    plot(sum(P2DG2,2))
    hold on
    centerAllFigures

%% 사각형 그리드로 보간
for slotIndex=1:4
BData=table2struct(WireTable(slotIndex,:));
xVar=BData.fieldxTimeTable.Variables;
yVar=BData.fieldyTimeTable.Variables;
xPos=BData.elementCentersTable.x';
yPos=BData.elementCentersTable.y';
[Fr,Ftheta]=cart2PolVector(xVar,yVar,xPos,yPos);
Bfield(slotIndex).Br         = Fr     
Bfield(slotIndex).Bthetam    = Ftheta   ;

for timeIndex=1:30:120
    % 요소 중심 좌표와 물리량 값을 Delaunay 객체에 할당
    DT_with_values = struct;
    DT_with_values.DT = DT;
    DT_with_values.ElementCenters = [m2mm(xPos)', m2mm(yPos)'];
    % DT_with_values.ElementValues = P2DG2(timeList(timeindex),:)';
    DT_with_values.ElementValues = abs(Fr(timeIndex,:))';
    
    figure(1)
    [Xq, Yq, Br,gridWidth,gridHeight]=interpolateTriToRect(DT_with_values);
    % DT_with_values.ElementValues = Ftheta(1,:)';
    % [Xq, Yq, Bt,gridWidth,gridHeight]=interpolateTriToRect(DT_with_values);
    hold on
    % refDim=[0.2 0.1 150]
    % refDim(1)=uniquetol(gridWidth,1e-1)
    % refDim(2)=uniquetol(gridHeight,1e-1)
    % refDim=[0.2 0.1 150]
    % hold on
    % [axisState,viewState,DataAspectRatio]=lockAxisAndView
    
end
ax=gca
axisState(5)=-0.1
restoreView(ax, axisState, viewState,DataAspectRatio)

figure(1)
MeshPlot=pdeplot(model.Mesh.Nodes,model.Mesh.Elements)
MeshPlot.Color=[0.80,0.80,0.80];  % grey
hold on
x = pdeNodes(1,:);
y = pdeNodes(2,:);
quadmesh(pdeQuadElements, x, y);

centerAllFigures
%% fatami eq 7
d_skinDepth=refDim(2)/calcSkinDepth(rpm2freqE(18000,4));
speed =18000
pole=8
Bfield.Br         = Br     
Bfield.Bthetam    = Bt   
surf(Xq, Yq, P2DG2);
[P1DG1P,P1DG2P,P2DG1P,P2DG2P,P2DG1,P2DG2,PrectP]  = calcHybridACLossWave('rectangular', refDim, rpm2freqE(speed,pole/2),Bfield);
figure(1)
for timeindex=1:1:len(timeList)
scatter3(m2mm(xPos),m2mm(yPos),P2DG2(timeList(timeindex),:),'MarkerEdgeColor',timeColorList{timeindex},'MarkerFaceColor','none','DisplayName',num2str(3*timeList(timeindex)-3))
hold on
end

figure(SlotFigIndex(slotIndex))
plot(sum(sum(P2DG2,"omitmissing")))
hold on
centerAllFigures



%%
    % 삼각형 요소의 개수 확인
    numElements = size(DT.ConnectivityList, 1);
    
    if length(elementValues) ~= numElements
        error('요소 개수와 요소 중심 물리량 값의 개수가 일치하지 않습니다.');
    end
    

    figure;
    triplot(DT);
    hold on;
    scatter(m2mm(xPos), m2mm(yPos), 50, DT_with_values.ElementValues, 'filled');
    colorbar;
    xlabel('X');
    ylabel('Y');
    title('삼각형 요소의 물리량 값 할당 및 시각화');