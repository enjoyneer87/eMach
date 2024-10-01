%% Table of Contents
% def Path
% Get PartStruct
% Get Wire Element and Node ID
% Load Mat File From JplotReader  need Do prior -with python Code
%%
% JmagResultName='e10MS_ConductorModel_REF_Load~16_';
JmagResultPath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\e10_v24.jfiles\ref_e10_Coil~16\ref_e10_Coil_Load~25'
% JmagResultPath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\e10MS_ConductorModel.jfiles\e10MS_ConductorModel_REF~3\e10MS_ConductorModel_REF_Load~8'
% JmagResultPath='D:\KangDH\Thesis\e10\JMAG\MSConductorModel\e10MS_ConductorModel.jfiles\e10MS_ConductorModel~6\e10MS_ConductorModel_SCL_Load~13';
% JmagResultName='e10MS_ConductorModel_SCL_Load~13';
[~,JmagResultName,~]=fileparts(JmagResultPath)
JmagResultDIR=extractBefore(JmagResultPath,'.jfiles');
[JmagPJTDIR,JmagPJTName,~]=fileparts(JmagResultDIR);
JmagPJTPath=fullfile(JmagPJTDIR,[JmagPJTName,'.jproj']);
%% Get PartStruct


% need 2 open Jproj
app=callJmag
app.Load(JmagPJTPath)
app.CheckForNewResults
PartStruct=getJMAGDesignerPartStruct(app);
Lactive=150
PartTable=struct2table(PartStruct);
BoolTargetSlot=contains(PartTable.Name,'Stator/')&(contains(PartTable.Name,'Region.2')|contains(PartTable.Name,'Wire'));

WireTable=PartTable(BoolTargetSlot,:);
WireTable = sortrows(WireTable,'Name'); 
LayerNumber=1
targetSlotNumber=6
targetPartIndex=LayerNumber*targetSlotNumber

%% Get Wire Element and Node ID
for SlotIndex=1:height(WireTable)
    WireIndex=WireTable.partIndex(SlotIndex);
    [ElementId{SlotIndex}, NodeID{SlotIndex},NodeTable{SlotIndex},DT{SlotIndex}]...
    =getMeshData(app,WireIndex);
end

% As Var 2 Table
WireTable.NodeTable=NodeTable';
WireTable.NodeID=NodeID';
WireTable.ElementId=ElementId';
WireTable.DT=DT';
% Backup
refWireTableBackup=WireTable;
%% Load Mat File From JplotReader -python
% DataStruct=load('ref_e10_WirePeriodic_Load_18k_rgh~32_Case28_MagB.mat')
if 38100==getPCRDPPortNumber
    matFileList=findMatFiles('D:\KangDH\Emlab_emach\tools\jmag\jplotReader')
else
    matFileList=findMatFiles('Z:\01_Codes_Projects\git_fork_emach\tools\jmag\jplotReader')
end
MagBmatFileList=matFileList(contains(matFileList,JmagResultName)&contains(matFileList,'MagB'))'
MagBmatFileList = sort(MagBmatFileList); 
[~,MatfileNames,~]=fileparts(MagBmatFileList)

for caseIndex=1:1
    WireTable=[];
    DataStruct=load(MagBmatFileList{caseIndex});
    %% Mapping 2 WireStruct > WireTable
    WireTable=mappingB2Slot(DataStruct,refWireTableBackup);
    WireTable=sortrows(WireTable,"Name","ascend");
    WireTable=cart2polPartTable(WireTable);
    save([MatfileNames{caseIndex},'_wireTable.mat'],"WireTable")
end

[axisState,viewState,DataAspectRatio]=lockAxisAndView()
restoreView(gca, axisState,viewState,DataAspectRatio)
%%
%% Create the Flux Density Fit 
load(MatfileNames{1})
for slotIndex=1:height(WireTable)
    % x=WireTable.elementCentersTable{slotIndex}.x;
    % y=WireTable.elementCentersTable{slotIndex}.y;
    x=WireTable.DT{slotIndex}.Points(:,1);
    y=WireTable.DT{slotIndex}.Points(:,2);
    a3rf=figure(3);
    a3rf.Name=['Br','_MS'];
    TR=triangulation(WireTable.elementCentersTable{slotIndex}.elementConnectivity,WireTable.DT{slotIndex}.Points);
    for timeIdx=1:2
     hold on
    Brvalues = WireTable.RtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
    % Brvalues = WireTable.fieldxTimeTable{slotIndex}(timeIdx,:).Variables;
    vertexValues = centroid2VertexValues(TR, Brvalues);
    TSTriSurf1(timeIdx)=trisurf(WireTable.DT{slotIndex}.ConnectivityList,x,y, abs(vertexValues), abs(vertexValues),'EdgeColor', 'none');
    end
    grid on
    box on
    colorbar('northoutside')
    setgcaXYcoor
    a4tf=figure(4);
    a4tf.Name=['Bt','_MS'];
    for timeIdx=1:120
    hold on
    % Btvalues = WireTable.fieldyTimeTable{slotIndex}(timeIdx,:).Variables;
    Btvalues = WireTable.TtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
    vertexBtValues = centroid2VertexValues(TR, Btvalues);
    TSTriSurf2(timeIdx)=trisurf(WireTable.DT{slotIndex}.ConnectivityList,x,y,abs(vertexBtValues) , abs(vertexBtValues),'EdgeColor', 'none');
    end
    grid on
    box on
    colorbar('northoutside')
    setgcaXYcoor
end

timeList=1:1:120;

C = linspecer(len(timeList));
for slotIndex=1:1
    % MVP=WireTable.fieldzTimeTable{slotIndex};
    DT=WireTable.DT{slotIndex};
    % triplot(DT)
    hold on
    % p, e, t로 변환
    p = DT.Points';  % p: 노드 좌표 (2 x N 형식, 전치 연산으로 변환)
    t = WireTable.elementCentersTable{slotIndex}.elementConnectivity';
    % e: 경계선 정보 생성
    edges = freeBoundary(DT);  % 자유 경계 (경계에 있는 점들)
    e = [edges'; zeros(2, size(edges, 1))];  % e: 경계선 정보 (4 x L 형식)
    msh.p=mm2m(p);
    msh.t=t;
    msh.e=e;
    TR=triangulation(WireTable.elementCentersTable{slotIndex}.elementConnectivity,DT.Points);
    % stem3(p(1,:),p(2,:),WireTable.fieldzTimeTable{slotIndex}(timeIndex,:).Variables')
    for timeIdx=1:len(timeList)
        % A=MVP(timeIndex,:).Variables;
    timeAngle=timeList(timeIdx);
    Bxvalues = WireTable.fieldxTimeTable{slotIndex}(timeAngle,:).Variables;
    Byvalues = WireTable.fieldyTimeTable{slotIndex}(timeAngle,:).Variables;
    % vertexBrValues = centroid2VertexValues(TR, Brvalues);
    % vertexBtValues = centroid2VertexValues(TR, Btvalues);
    % B=[B;zeros(len(B),1)'];
    aq=quiver3Jmag(TR,[Bxvalues', Byvalues', zeros(len(Bxvalues'),1)]);
    aq.Color=C(timeIdx,:);
    % DT.(DT.incenter)
    % IC=TR.incenter;
    % trisurf(TR.ConnectivityList,TR.Points(:,1),TR.Points(:,2),abs(vertexValues),abs(vertexValues))
    % h=drawFluxDensity(msh,A(:,timeIndex))
    hold on
    end
    % [linehandles, linecoordinates] = drawFluxLines(msh, Babs_t, 20,'k')
end

ax=gca
ax.XLim=[80 91]
ax.Colormap=C
colorbar('northoutside')
aMesh=triplot(DT)
aMesh.Color=greyColor


legend([num2str(timeList*3),'[deg]'])
% 
% % 
% % %% From A
% for slotIndex=1:height(WireTable)
%     % MVP=WireTable.fieldzTimeTable{slotIndex};
%     DT=WireTable.DT{slotIndex};
%     % triplot(DT)
%     hold on
%     % p, e, t로 변환
%     p = DT.Points';  % p: 노드 좌표 (2 x N 형식, 전치 연산으로 변환)
%     t = WireTable.elementCentersTable{slotIndex}.elementConnectivity';
%     % e: 경계선 정보 생성
%     edges = freeBoundary(DT);  % 자유 경계 (경계에 있는 점들)
%     e = [edges'; zeros(2, size(edges, 1))];  % e: 경계선 정보 (4 x L 형식)
%     msh.p=mm2m(p);
%     msh.t=t;
%     msh.e=e;
%     TR=triangulation(WireTable.elementCentersTable{slotIndex}.elementConnectivity,DT.Points);
%     % stem3(p(1,:),p(2,:),WireTable.fieldzTimeTable{slotIndex}(timeIndex,:).Variables')
%     for timeIdx=1:2:120
%         % A=MVP(timeIndex,:).Variables;
% 
%     Btvalues = WireTable.TtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
%     Brvalues = WireTable.RtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
%     vertexValues = centroid2VertexValues(TR, Brvalues);
%     vertexBtValues = centroid2VertexValues(TR, Btvalues);
% 
%     % u=WireTable.fieldxTimeTable{slotIndex}.Variables';
%     % v=WireTable.fieldyTimeTable{slotIndex}.Variables';
%     % w=WireTable.fieldzTimeTable{slotIndex}.Variables';
%     % elementCurl = computeCurl3D(TR,u(:,timeIndex),v(:,timeIndex),w(:,timeIndex));
%     % [Babs_t,B] = calculate_B(A', msh);
% 
%     vertexValues = centroid2VertexValues(TR, Babs_t);
%     % B=[B;zeros(len(B),1)'];
%     quiver3Jmag(TR,B');
%     % DT.(DT.incenter)
%     IC=TR.incenter;
%     trisurf(TR.ConnectivityList,TR.Points(:,1),TR.Points(:,2),abs(vertexValues),abs(vertexValues))
%     % h=drawFluxDensity(msh,A(:,timeIndex))
%     hold on
%     end
%     % [linehandles, linecoordinates] = drawFluxLines(msh, Babs_t, 20,'k')
% end
% 
%     % triSurfPet(msh, MVP(50,:).Variables'); 
% 
% % 메쉬를 p, e, t 형식으로 플롯
% % triplot(t',p(1,:)',p(2,:)');
% % axis equal;  % 축을 동일한 비율로 설정
% % hold on
%     hold on
%     triplot(WireTable.DT{slotIndex})
% 
%     Babs_t = calculate_B(MVP(timeIndex,:).Variables', msh);
%     stem3(WireTable.elementCentersTable{slotIndex}.x,WireTable.elementCentersTable{slotIndex}.y,Babs_t')
% end
% 
% for slotIndex=1:6
% 
% 
% hold on
% end
% IC=TR.incenter
% % 각 삼각형의 중심점에서 계산된 curl 값을 해당 삼각형 꼭짓점에 적용
% for i = 1:size(triangles, 1)
%     % 삼각형의 꼭짓점 인덱스
%     vertexIndices = triangles(i, :);
% 
%     % 각 꼭짓점에 해당하는 z 값을 elementCurl로 설정
%     Z(vertexIndices) = elementCurl(i);
% end
% ax=newplot
% trisurf(triangles, points(:, 1), points(:, 2), Z, 'FaceColor', 'interp', 'EdgeColor', 'none');
% 
% 
% %% Mesh Export
% % MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/REF_e10_WTPM_PatternD_TS_case28.csv'
% MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/MPtools_SCL_e10_WTPM_PatternD_TS_case28.csv'
% % [model, pdeTriElements, pdeNodes, pdeQuadElements, quadElementsId, combinedElements,FieldDataSteps]= nastran2PDEMesh(MPToolCSVFilePath,'mm');
%  % [SCL_TSMesh,model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath,'mm')
% % save('SCL_TS_18krpm_case28_Mesh.mat','SCL_TSMesh');
