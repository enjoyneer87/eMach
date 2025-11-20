%% get Dta
matFileList=findMatFiles(pwd)';
matFileList=matFileList(contains(matFileList,'wire'));
REFmatFileList=matFileList(contains(matFileList,'SC'));
REFmatFileList=REFmatFileList(contains(REFmatFileList,'MagB'));
REFDTmatFileList=REFmatFileList(~contains(REFmatFileList,'DT'));
REFDTmatFileList=REFDTmatFileList(contains(REFDTmatFileList,'Case28'));
% REFDTmatFileList=REFDTmatFileList(~contains(REFDTmatFileList,'18k'));

% FqmatFileList=REFDTmatFileList(contains(REFDTmatFileList,'Fq'));
% MSmatFileList=REFDTmatFileList(contains(REFDTmatFileList,'MS'));
matFileList=REFDTmatFileList

[~,MatfileNames,~]=fileparts(REFDTmatFileList);

close all
for idx=1:1
    load(MatfileNames{idx,1})
    if contains(MatfileNames{idx},'fq',IgnoreCase=true)
        simuType='FQ'
    elseif contains(MatfileNames{idx},'MS',IgnoreCase=true)
        simuType='MS'
    else
        simuType='TS'
    end
    for slotIndex=1:height(WireFitTable)
    x=WireFitTable.DT{slotIndex}.Points(:,1);
    y=WireFitTable.DT{slotIndex}.Points(:,2);
        a3rf=figure(3);
        a3rf.Name=['Br',simuType];
        for timeIdx=1:121
         hold on
        Brvalues = WireFitTable.RtileTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        TSTriSurf1(timeIdx)=trisurf(WireFitTable.DT{slotIndex}.ConnectivityList,x,y, abs(Brvalues), abs(Brvalues),'EdgeColor', 'none');

        end
        a4tf=figure(4);
        a4tf.Name=['Bt',simuType];
        for timeIdx=1:121
        hold on
        Btvalues = WireFitTable.TtileTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        TSTriSurf2(timeIdx)=trisurf(WireFitTable.DT{slotIndex}.ConnectivityList,x,y, abs(Btvalues), abs(Btvalues),'EdgeColor', 'none');
        end
    end
end
ax=TSTriSurf1(1).Parent
ax2=TSTriSurf2(1).Parent
ax.Colormap=parula
ax2.Colormap=parula;       

% 
% ax=ax.Parent
%         ax2=ax2.Parent
%         ax.Colormap=thermal
%         ax2.Colormap=thermal;
        % 
        % freezeColors(ax);
        % freezeColors(colorbar)
        % freezeColors(ax2);
        % freezeColors(colorbar)

% D:\KangDH\Emlab_emach\mlxperPJT\JEET\devSurfInterp4TS.m

for idx=2:2
    load(MatfileNames{idx,1})
    if contains(MatfileNames{idx},'fq',IgnoreCase=true)
        simuType='FQ'
    elseif contains(MatfileNames{idx},'MS',IgnoreCase=true)
        simuType='MS'
    else
        simuType='TS'
    end
    for slotIndex=1:height(WireTable)
    x=WireTable.DT{slotIndex}.Points(:,1);
    y=WireTable.DT{slotIndex}.Points(:,2);
        a1rf=figure(1);
        a1rf.Name=['Br',simuType];     
      
        for timeIdx=4:4
         hold on
        Brvalues = WireTable.RtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        trisurf(WireTable.DT{slotIndex}.ConnectivityList,x,y, abs(Brvalues), abs(Brvalues),'FaceColor','interp')
        end
        a2tf=figure(2);
        a2tf.Name=['Bt',simuType];
        
        for timeIdx=4:4
        hold on
        Btvalues = WireTable.TtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        trisurf(WireTable.DT{slotIndex}.ConnectivityList,x,y, abs(Btvalues), abs(Btvalues),'FaceColor','interp')
        end
    end
end





idx=2
load(matFileList{idx,1})
if contains(matFileList{idx},'fq',IgnoreCase=true)
    simuType='FQ'
elseif contains(matFileList{idx},'MS',IgnoreCase=true)
    simuType='MS'
else
    simuType='TS'
end
for slotIndex = 1:height(WireTable)

    x = WireTable.DT{slotIndex}.Points(:,1);
    y = WireTable.DT{slotIndex}.Points(:,2);
    TR = WireTable.DT{slotIndex};  % triangulation 객체
    eleType = WireTable.RtimeTableByElerow{slotIndex}.eleType;
    eleCenter = [WireTable.RtimeTableByElerow{slotIndex}.x, WireTable.RtimeTableByElerow{slotIndex}.y];
    sizeFieldData=size(WireTable.fieldxTimeTable{1})
    a1rf=figure(1);
    a1rf.Name=['Br',simuType];
    triplot(WireTable.DT{slotIndex})
    hold on
    % title('Br Field');
    for timeIdx = 1:sizeFieldData(1)
        Brvalues = WireTable.RtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        vertexValues = centroid2VertexValues(TR, eleType, eleCenter, Brvalues');  % 삼각형 및 사각형 모두 처리
        trisurf(TR.ConnectivityList, x, y, abs(vertexValues), abs(vertexValues), 'EdgeColor', 'none');
    end
    a2tf=figure(2);
    a2tf.Name=['Bt',simuType];
     triplot(WireTable.DT{slotIndex})
    hold on
    % title('Bt Field');
    for timeIdx = 1:sizeFieldData(1)
        Btvalues = WireTable.TtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        vertexBtValues = centroid2VertexValues(TR, eleType, eleCenter, Btvalues');
        tsurf2(timeIdx)=trisurf(TR.ConnectivityList, x, y, abs(vertexBtValues), abs(vertexBtValues), 'EdgeColor', 'none');
        tsurf2(timeIdx).FaceAlpha  =timeIdx/sizeFieldData(1);

    end
end



for idx=1:1
    load(MatfileNames{idx,1})
    if contains(MatfileNames{idx},'fq',IgnoreCase=true)
        simuType='FQ'
    elseif contains(MatfileNames{idx},'MS',IgnoreCase=true)
        simuType='MS'
    else
        simuType='TS'
    end
    for slotIndex=1:height(WireFitTable)
    x=WireFitTable.DT{slotIndex}.Points(:,1);
    y=WireFitTable.DT{slotIndex}.Points(:,2);
        a1rf=figure(1);
        a1rf.Name=['Br',simuType];   

        for timeIdx=1:240
         hold on
        Brvalues = WireFitTable.RtileTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx+240));
        tsurf1(timeIdx)=trisurf(WireFitTable.DT{slotIndex}.ConnectivityList,x,y, abs(Brvalues), abs(Brvalues),'EdgeColor', 'none');
        tsurf1(timeIdx).FaceAlpha  =timeIdx/240;
        end
        a2tf=figure(2);
        a2tf.Name=['Bt',simuType];
        for timeIdx=1:240
        hold on
        Btvalues = WireFitTable.TtileTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx+240));
        tsurf2(timeIdx)=trisurf(WireFitTable.DT{slotIndex}.ConnectivityList,x,y, abs(Btvalues), abs(Btvalues),'EdgeColor', 'none');
        tsurf2(timeIdx).FaceAlpha  =timeIdx/240;
        end
    end
end

        tsurf2(timeIdx)=trisurf(WireFitTable.DT{slotIndex}.ConnectivityList,x,y, abs(Btvalues), abs(Btvalues),'EdgeColor', 'none');
%% Lus plot

load(REFDTmatFileList{2})
timeList=1:1:241;

C = linspecer(len(timeList));
for slotIndex=1:4
    % MVP=WireTable.fieldzTimeTable{slotIndex};
    % DT=WireTable.DT{slotIndex};
    % triplot(DT)
    % hold on
    % % p, e, t로 변환
    % p = DT.Points';  % p: 노드 좌표 (2 x N 형식, 전치 연산으로 변환)
    % t = WireTable.elementCentersTable{slotIndex}.elementConnectivity';
    % % e: 경계선 정보 생성
    % edges = freeBoundary(DT);  % 자유 경계 (경계에 있는 점들)
    % e = [edges'; zeros(2, size(edges, 1))];  % e: 경계선 정보 (4 x L 형식)
    % msh.p=mm2m(p);
    % msh.t=t;
    % msh.e=e;
    % TR=WireTable.DT{slotIndex};

    amesh=triplot(WireTable.DT{slotIndex});
    amesh.Color=greyColor();
    hold on
    % TR=triangulation(WireTable.elementCentersTable{slotIndex}.elementConnectivity,DT.Points);
    % stem3(p(1,:),p(2,:),WireTable.fieldzTimeTable{slotIndex}(timeIndex,:).Variables')
    for timeIdx=1:241
        % A=MVP(timeIndex,:).Variables;
    timeAngle=timeList(timeIdx);
    Bxvalues = WireTable.fieldxTimeTable{slotIndex}(timeIdx,:).Variables;
    Byvalues = WireTable.fieldyTimeTable{slotIndex}(timeIdx,:).Variables;
    % vertexBrValues = centroid2VertexValues(TR, Brvalues);
    % vertexBtValues = centroid2VertexValues(TR, Btvalues);
    % B=[B;zeros(len(B),1)'];
    aq=quiver(WireTable.elementCentersTable{slotIndex}.x,WireTable.elementCentersTable{slotIndex}.y,Bxvalues',Byvalues');
    % aq=quiver3Jmag(TR,[Bxvalues', Byvalues', zeros(len(Bxvalues'),1)]);

    centroids=[WireTable.elementCentersTable{slotIndex}.x,WireTable.elementCentersTable{slotIndex}.y];
    % Bxvalues',Byvalues'
    elementCurl=[Bxvalues', Byvalues', zeros(len(Bxvalues'),1)];
    % 중심점 좌표 (x, y)에서 벡터 그리기
    % aq=quiver3(centroids(:, 1), centroids(:, 2), zeros(size(centroids, 1), 1), ...  % 벡터 시작점
    %     elementCurl(:,1), elementCurl(:,2), elementCurl(:,3), ...  % 벡터 방향 (z 방향으로만 표시)
    %     'AutoScale', 'on', 'LineWidth', 1);  % z 방향으로 크기를 elementCurl 값에 비례하게 표시

    aq.Color=C(timeIdx,:);
    % DT.(DT.incenter)
    % IC=TR.incenter;
    % trisurf(TR.ConnectivityList,TR.Points(:,1),TR.Points(:,2),abs(vertexValues),abs(vertexValues))
    % h=drawFluxDensity(msh,A(:,timeIndex))
    hold on
    end
    % [linehandles, linecoordinates] = drawFluxLines(msh, Babs_t, 20,'k')
end
ax=aq.Parent
ax.Colormap=C
colorbar(ax,'northoutside')


% ax=tsurf1(1).Parent
% ax2=tsurf2(1).Parent
% ax.Colormap=thermal
% ax2.Colormap=thermal;

% freezeColors(ax);
% freezeColors(colorbar)
% freezeColors(ax2);
% freezeColors(colorbar)

% ax2.f

%% Coil Model
matFileList    =findMatFiles(pwd)';                              
matFileList    =matFileList(contains(matFileList,'_wireTable.'));
CoilFile    =matFileList(contains(matFileList,'Coil'));
matFileList    =matFileList(contains(matFileList,'Conductor'));
matFileList    =matFileList(contains(matFileList,'Case28'));

[~,MatfileNames,~]=fileparts(matFileList);
timeStepReducedFactor=1;  % 480 step -> 240 = 2
% triangulations = partitionedTriangulation(WireTable);
grey=greyColor();
%% Create the Flux Density Fit 
idx=1
load(matFileList{idx})
if contains(matFileList{idx},'fq',IgnoreCase=true)
    simuType='FQ'
elseif contains(matFileList{idx},'MS',IgnoreCase=true)
    simuType='MS'
else
    simuType='TS'
end
C = linspecer(sizeFieldData(1));

for slotIndex = 1:height(WireTable)

    x = WireTable.DT{slotIndex}.Points(:,1);
    y = WireTable.DT{slotIndex}.Points(:,2);
    TR = WireTable.DT{slotIndex};  % triangulation 객체
    eleType = WireTable.RtimeTableByElerow{slotIndex}.eleType;
    eleCenter = [WireTable.RtimeTableByElerow{slotIndex}.x, WireTable.RtimeTableByElerow{slotIndex}.y];
    sizeFieldData=size(WireTable.fieldxTimeTable{1})
    a1rf=figure(1);
    a1rf.Name=['Br',simuType];
    triplot(WireTable.DT{slotIndex})
    hold on
    % title('Br Field');
    for timeIdx = 1:sizeFieldData(1)
        Brvalues = WireTable.RtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        vertexValues = centroid2VertexValues(TR, eleType, eleCenter, Brvalues');  % 삼각형 및 사각형 모두 처리
        trisurf(TR.ConnectivityList, x, y, abs(vertexValues), abs(vertexValues), 'EdgeColor', C(timeIdx,:));
    end
    a2tf=figure(2);
    a2tf.Name=['Bt',simuType];
     triplot(WireTable.DT{slotIndex})
    hold on
    % title('Bt Field');
    for timeIdx = 1:sizeFieldData(1)
        Btvalues = WireTable.TtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        vertexBtValues = centroid2VertexValues(TR, eleType, eleCenter, Btvalues');
        tsurf2(timeIdx)=trisurf(TR.ConnectivityList, x, y, abs(vertexBtValues), abs(vertexBtValues), 'EdgeColor', C(timeIdx,:));
        tsurf2(timeIdx).FaceAlpha  =timeIdx/sizeFieldData(1);
    end
end


for slotIndex = 1:height(WireTable)

    x = WireTable.DT{slotIndex}.Points(:,1);
    y = WireTable.DT{slotIndex}.Points(:,2);

    % x = WireTable.elementCentersTable{slotIndex}.x;
    % y = WireTable.elementCentersTable{slotIndex}.y;

    for timeIdx = 1:sizeFieldData(1)
        Btvalues = WireTable.ZtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        scatter3(x,y,Btvalues)
        hold on
    end
end


idx=1
load(CoilFile{idx})
if contains(matFileList{idx},'fq',IgnoreCase=true)
    simuType='FQ'
elseif contains(matFileList{idx},'MS',IgnoreCase=true)
    simuType='MS'
else
    simuType='TS'
end
for slotIndex = 1:height(WireTable)

    x = WireTable.DT{slotIndex}.Points(:,1);
    y = WireTable.DT{slotIndex}.Points(:,2);
    TR = WireTable.DT{slotIndex};  % triangulation 객체
    eleType = WireTable.RtimeTableByElerow{slotIndex}.eleType;
    eleCenter = [WireTable.RtimeTableByElerow{slotIndex}.x, WireTable.RtimeTableByElerow{slotIndex}.y];
    sizeFieldData=size(WireTable.fieldxTimeTable{1})
    a1rf=figure(1);
    a1rf.Name=['Br',simuType];
    triplot(WireTable.DT{slotIndex})
    hold on
    % title('Br Field');
    for timeIdx = 1:sizeFieldData(1)
        Brvalues = WireTable.RtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        vertexValues = centroid2VertexValues(TR, eleType, eleCenter, Brvalues');  % 삼각형 및 사각형 모두 처리
        trisurf(TR.ConnectivityList, x, y, abs(vertexValues), abs(vertexValues), 'EdgeColor', 'none');
    end
    a2tf=figure(2);
    a2tf.Name=['Bt',simuType];
     triplot(WireTable.DT{slotIndex})
    hold on
    % title('Bt Field');
    for timeIdx = 1:sizeFieldData(1)
        Btvalues = WireTable.TtimeTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        vertexBtValues = centroid2VertexValues(TR, eleType, eleCenter, Btvalues');
        tsurf2(timeIdx)=trisurf(TR.ConnectivityList, x, y, abs(vertexBtValues), abs(vertexBtValues), 'EdgeColor', 'none');
        tsurf2(timeIdx).FaceAlpha  =timeIdx/sizeFieldData(1);
    end
end




for slotIndex=1:height(WireTable)
triplot(WireTable.DT{slotIndex})
hold on
scatter(WireTable.elementCentersTable{slotIndex}.x,WireTable.elementCentersTable{slotIndex}.y,'*')
scatter(WireTable.DT{slotIndex}.Points(WireTable.elementCentersTable{slotIndex}.elementConnectivity',1),WireTable.DT{slotIndex}.Points(WireTable.elementCentersTable{slotIndex}.elementConnectivity',2))

end