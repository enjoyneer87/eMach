%% Table of Contents
% def Path
% Get PartStruct
% Get Wire Element and Node ID
% Load Mat File From JplotReader  need Do prior -with python Code
%%
% JmagResultName='e10MS_ConductorModel_REF_Load~16_';
JmagResultPath='E:\KDH\e10\MSConductorModel\e10MS_ConductorModel.jfiles\e10MS_ConductorModel~6\e10MS_ConductorModel_SCL_Load~13'
% JmagResultPath='F:\KDH\KDH\SCL_e10_WTPM_PatternD_R1_4k.jfiles\SC_e10_WirePeriodic~9\SC_e10_WirePeriodic_Load_4k_rough~26'
% JmagResultPath='F:\KDH\KDH\SCL_e10_WTPM_PatternD_R1_16kMap.jfiles\SC_e10_WirePeriodic~9\SC_e10_WirePeriodic_Load_16k_rough~27';
% JmagResultName='e10MS_ConductorModel_SCL_Load~13';
[~,JmagResultName,~]=fileparts(JmagResultPath);
JmagResultDIR=extractBefore(JmagResultPath,'.jfiles');
[JmagPJTDIR,JmagPJTName,~]=fileparts(JmagResultDIR);
JmagPJTPath=fullfile(JmagPJTDIR,[JmagPJTName,'.jproj']);
%% Get PartStruct


% need 2 open Jproj
app=callJmag
app.Show
app.Load(JmagPJTPath)
PartStruct=getJMAGDesignerPartStruct(app);
Lactive=150;
PartTable=struct2table(PartStruct);
BoolTargetSlot=contains(PartTable.Name,'Slot1/')|contains(PartTable.Name,'Slot2/');
WireTable=PartTable(BoolTargetSlot,:);
WireTable = sortrows(WireTable,'Name'); 
LayerNumber=4;
targetSlotNumber=2;
targetPartIndex=LayerNumber*targetSlotNumber;

savePartIDToMat(WireTable.partIndex, JmagPJTPath)

%% Get Wire Element and Node ID
for SlotIndex=1:height(WireTable)
    WireIndex=WireTable.partIndex(SlotIndex);
    [ElementId{SlotIndex}, NodeID{SlotIndex},NodeTable{SlotIndex},delaunyObj{SlotIndex}]...
    =getMeshData(app,WireIndex);
end




% As Var 2 Table
WireTable.NodeTable=NodeTable';
WireTable.NodeID=NodeID';
WireTable.ElementId=ElementId';
WireTable.DT=delaunyObj';



% Backup
refWireTableBackup=WireTable;
%% Load Mat File From JplotReader 
% -python
% DataStruct=load('ref_e10_WirePeriodic_Load_18k_rgh~32_Case28_MagB.mat')
if 38100==getPCRDPPortNumber
    matFileList=findMatFiles('D:\KangDH\Emlab_emach\tools\jmag\jplotReader');
else
    matFileList=findMatFiles('Z:\01_Codes_Projects\git_fork_emach\tools\jmag\jplotReader');
end
MagBmatFileList=matFileList(contains(matFileList,JmagResultName)&contains(matFileList,'MagB')&~contains(matFileList,'backup','IgnoreCase',true));
MagBmatFileList = sort(MagBmatFileList); 
[~,MatfileNames,~]=fileparts(MagBmatFileList);
% for caseIndex=1:len(MatfileNames)

parpool;  % 병렬 풀 시작 (필요한 경우)

% WireTable의 결과를 저장할 셀 배열 선언
WireTableResults = cell(1, 30);

parfor caseIndex = 1:30  % 'parfor'를 사용하여 병렬 처리
    % 초기화
    WireTable = [];
    
    % 데이터 로드
    DataStruct = load(MagBmatFileList{caseIndex});
    
    %% Mapping 2 WireStruct > WireTable
    WireTable = mappingB2Slot(DataStruct, refWireTableBackup);  % WireTable 생성
    WireTable = sortrows(WireTable, "Name", "ascend");  % 정렬
    WireTable = cart2polPartTable(WireTable);  % 좌표 변환
    
    WireTable=removevars(WireTable,'object')
    % 결과를 셀 배열에 저장
    WireTableResults{caseIndex} = WireTable;
end

delete(gcp('nocreate'));  % 병렬 풀 종료 (필요한 경우)

% 병렬 작업 완료 후 순차적으로 저장
for caseIndex = 1:30
    WireTable = WireTableResults{caseIndex};  % 병렬 결과 불러오기
    save([MatfileNames{caseIndex}, '_wireTable.mat'], 'WireTable');  % 저장
end
%% Mesh Export
% MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/REF_e10_WTPM_PatternD_TS_case28.csv'
% MPToolCSVFilePath='D:/KangDH/Emlab_emach/mlxperPJT/JEET/From38100/MPtools_SCL_e10_WTPM_PatternD_TS_case28.csv'
% [model, pdeTriElements, pdeNodes, pdeQuadElements, quadElementsId, combinedElements,FieldDataSteps]= nastran2PDEMesh(MPToolCSVFilePath,'mm');
 % [SCL_TSMesh,model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath,'mm')
% save('SCL_TS_18krpm_case28_Mesh.mat','SCL_TSMesh');
% 
% for index=1:500
% 
%     al=plot(WireTable.fieldxTimeTable{1,1}.(1))
%     hold on
%     plot(x)
%     ax=al.Parent
%     ax.YLim=[-0.05 0.05]
%         pause(0.1);  % 0.1초 동안 일시정지 (속도를 조절할 수 있습니다)
%     drawnow;  % 그래프를 즉시 업데이트
% 
%      % hold on
% end
% 
% 
% %% Create the Flux Density Fit 
% load('SC_e10_WirePeriodic_Load_16k_rough~27_Case78_MagB_wireTable.mat')
% % load('SC_e10_WirePeriodic_Load_16k_rough~27_Case27_MagB_wireTable.mat')
% for slotIndex=1:height(WireTable)
%     % x=WireTable.elementCentersTable{slotIndex}.x;
%     % y=WireTable.elementCentersTable{slotIndex}.y;
%     x=WireTable.DT{slotIndex}.Points(:,1);
%     y=WireTable.DT{slotIndex}.Points(:,2);
%     a3rf=figure(3);
%     a3rf.Name=['Br','_TS'];
%     % elementConnectivityMat=cell2matwithvaryCell(WireTable.elementCentersTable{slotIndex}.elementConnectivity);
%     TR=WireTable.DT{slotIndex};
%     eleType=WireTable.RtimeTableByElerow{slotIndex}.eleType;
%     eleCenter=[WireTable.RtimeTableByElerow{slotIndex}.x, WireTable.RtimeTableByElerow{slotIndex}.y];
%     % TR=triangulation(elementConnectivityMat,WireTable.DT{slotIndex}.Points);
%     for timeIdx=1:240
%      hold on
%     Brvalues = WireTable.RtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
%     % Brvalues = WireTable.fieldxTimeTable{slotIndex}(timeIdx,:).Variables;
%     vertexValues = centroid2VertexValues(TR,eleType,eleCenter,Brvalues');
%     TSTriSurf1(timeIdx)=trisurf(TR.ConnectivityList,x,y, abs(vertexValues), abs(vertexValues),'EdgeColor', 'none');
%     end
%     % grid on
%     % box on
%     % colorbar('northoutside')
%     % setgcaXYcoor
%     a4tf=figure(4);
%     a4tf.Name=['Bt','_TS'];
%     for timeIdx=1:240
%     hold on
%     % Btvalues = WireTable.fieldyTimeTable{slotIndex}(timeIdx,:).Variables;
%     Btvalues = WireTable.TtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx)); 
%     vertexBtValues = centroid2VertexValues(TR,eleType,eleCenter, Btvalues);
%     TSTriSurf2(timeIdx)=trisurf(TR.ConnectivityList,x,y,abs(vertexBtValues) , abs(vertexBtValues),'EdgeColor', 'none');
%     end
%     % grid on
%     % box on
%     % colorbar('northoutside')
%     % setgcaXYcoor
% end

% idx=1
% load(matFileList{idx,1})
% 
% for slotIndex = 1:height(WireTable)
%     x = WireTable.DT{slotIndex}.Points(:,1);
%     y = WireTable.DT{slotIndex}.Points(:,2);
%     TR = WireTable.DT{slotIndex};  % triangulation 객체
%     eleType = WireTable.RtimeTableByElerow{slotIndex}.eleType;
%     eleCenter = [WireTable.RtimeTableByElerow{slotIndex}.x, WireTable.RtimeTableByElerow{slotIndex}.y];
% 
%     figure(3); hold on;
%     title('Br Field');
%     for timeIdx = 1:241
%         Brvalues = WireTable.RtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
%         vertexValues = centroid2VertexValues(TR, eleType, eleCenter, Brvalues');  % 삼각형 및 사각형 모두 처리
%         trisurf(TR.ConnectivityList, x, y, abs(vertexValues), abs(vertexValues), 'EdgeColor', 'none');
%     end
% 
%     figure(4); hold on;
%     title('Bt Field');
%     for timeIdx = 1:241
%         Btvalues = WireTable.TtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
%         vertexBtValues = centroid2VertexValues(TR, eleType, eleCenter, Btvalues');
%         trisurf(TR.ConnectivityList, x, y, abs(vertexBtValues), abs(vertexBtValues), 'EdgeColor', 'none');
%     end
% end
% % %% quiver
% timeList=241:1:480;
% 
% C = linspecer(len(timeList));
% for slotIndex=1:8
%     % MVP=WireTable.fieldzTimeTable{slotIndex};
%     % DT=WireTable.DT{slotIndex};
%     % triplot(DT)
%     % hold on
%     % % p, e, t로 변환
%     % p = DT.Points';  % p: 노드 좌표 (2 x N 형식, 전치 연산으로 변환)
%     % t = WireTable.elementCentersTable{slotIndex}.elementConnectivity';
%     % % e: 경계선 정보 생성
%     % edges = freeBoundary(DT);  % 자유 경계 (경계에 있는 점들)
%     % e = [edges'; zeros(2, size(edges, 1))];  % e: 경계선 정보 (4 x L 형식)
%     % msh.p=mm2m(p);
%     % msh.t=t;
%     % msh.e=e;
%     % TR=WireTable.DT{slotIndex};
% 
%     % TR=triangulation(WireTable.elementCentersTable{slotIndex}.elementConnectivity,DT.Points);
%     % stem3(p(1,:),p(2,:),WireTable.fieldzTimeTable{slotIndex}(timeIndex,:).Variables')
%     for timeIdx=1
%         % A=MVP(timeIndex,:).Variables;
%     timeAngle=timeList(timeIdx);
%     Bxvalues = WireTable.fieldxTimeTable{slotIndex}(timeIdx,:).Variables;
%     Byvalues = WireTable.fieldyTimeTable{slotIndex}(timeIdx,:).Variables;
%     % vertexBrValues = centroid2VertexValues(TR, Brvalues);
%     % vertexBtValues = centroid2VertexValues(TR, Btvalues);
%     % B=[B;zeros(len(B),1)'];
%     aq=quiver(WireTable.elementCentersTable{slotIndex}.x,WireTable.elementCentersTable{slotIndex}.y,Bxvalues',Byvalues');
%     % aq=quiver3Jmag(TR,[Bxvalues', Byvalues', zeros(len(Bxvalues'),1)]);
% 
%     centroids=[WireTable.elementCentersTable{slotIndex}.x,WireTable.elementCentersTable{slotIndex}.y];
%     % Bxvalues',Byvalues'
%     elementCurl=[Bxvalues', Byvalues', zeros(len(Bxvalues'),1)];
%     % 중심점 좌표 (x, y)에서 벡터 그리기
%     % aq=quiver3(centroids(:, 1), centroids(:, 2), zeros(size(centroids, 1), 1), ...  % 벡터 시작점
%     %     elementCurl(:,1), elementCurl(:,2), elementCurl(:,3), ...  % 벡터 방향 (z 방향으로만 표시)
%     %     'AutoScale', 'on', 'LineWidth', 1);  % z 방향으로 크기를 elementCurl 값에 비례하게 표시
% 
%     aq.Color=C(timeIdx,:);
%     % DT.(DT.incenter)
%     % IC=TR.incenter;
%     % trisurf(TR.ConnectivityList,TR.Points(:,1),TR.Points(:,2),abs(vertexValues),abs(vertexValues))
%     % h=drawFluxDensity(msh,A(:,timeIndex))
%     hold on
%     end
%     % [linehandles, linecoordinates] = drawFluxLines(msh, Babs_t, 20,'k')
% end
% 
% 
% for slotIndex=1:height(WireTable)
% 
%     for timeIdx=1:240
%     Btvalues = WireTable.TtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx)); 
% 
%     scatter3(WireTable.TtimeTableByElerow{slotIndex}.x,WireTable.TtimeTableByElerow{slotIndex}.y,Btvalues)
%     hold on
%     end
% end