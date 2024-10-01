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
for idx=3:3
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
        Brvalues = WireTable.RtileTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        trisurf(WireTable.DT{slotIndex}.ConnectivityList,x,y, abs(Brvalues), abs(Brvalues),'FaceColor','interp')
        end
        a2tf=figure(2);
        a2tf.Name=['Bt',simuType];
        
        for timeIdx=4:4
        hold on
        Btvalues = WireTable.TtileTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
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
matFileList    =matFileList(contains(matFileList,'_wireTable'));
[~,MatfileNames,~]=fileparts(matFileList);
timeStepReducedFactor=1;  % 480 step -> 240 = 2
% triangulations = partitionedTriangulation(WireTable);
grey=greyColor();
%% Create the Flux Density Fit 
load(MatfileNames{2})
for slotIndex=1:height(WireTable)
    % x=WireTable.elementCentersTable{slotIndex}.x;
    % y=WireTable.elementCentersTable{slotIndex}.y;
    x=WireTable.DT{slotIndex}.Points(:,1);
    y=WireTable.DT{slotIndex}.Points(:,2);
    a3rf=figure(3);
    a3rf.Name=['Br','_MS'];
    TR=triangulation(WireTable.elementCentersTable{slotIndex}.elementConnectivity,WireTable.DT{slotIndex}.Points);
    for timeIdx=1:120
     hold on
    Brvalues = WireTable.RtileTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
    vertexValues = centroid2VertexValues(TR, Brvalues);
    TSTriSurf1(timeIdx)=trisurf(WireTable.DT{slotIndex}.ConnectivityList,x,y, abs(vertexValues), abs(vertexValues),'EdgeColor', 'none');
    end
    
    a4tf=figure(4);
    a4tf.Name=['Bt','_MS'];
    for timeIdx=1:120
    hold on
    Btvalues = WireTable.TtileTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
    vertexBtValues = centroid2VertexValues(TR, Btvalues);
    TSTriSurf2(timeIdx)=trisurf(WireTable.DT{slotIndex}.ConnectivityList,x,y,abs(vertexBtValues) , abs(vertexBtValues),'EdgeColor', 'none');
    end
end


for slotIndex=1:height(WireTable)
triplot(WireTable.DT{slotIndex})
hold on
scatter(WireTable.elementCentersTable{slotIndex}.x,WireTable.elementCentersTable{slotIndex}.y,'*')
scatter(WireTable.DT{slotIndex}.Points(WireTable.elementCentersTable{slotIndex}.elementConnectivity',1),WireTable.DT{slotIndex}.Points(WireTable.elementCentersTable{slotIndex}.elementConnectivity',2))

end