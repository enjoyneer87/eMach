%% get Dta
matFileList=findMatFiles(pwd)';
matFileList=matFileList(contains(matFileList,'wire'));
REFmatFileList=matFileList(contains(matFileList,'SC'));
REFmatFileList=REFmatFileList(contains(REFmatFileList,'MagB'));
REFDTmatFileList=REFmatFileList(contains(REFmatFileList,'DT'));
REFDTmatFileList=REFDTmatFileList(contains(REFDTmatFileList,'Case17'));
REFDTmatFileList=REFDTmatFileList(~contains(REFDTmatFileList,'18k'));

% FqmatFileList=REFDTmatFileList(contains(REFDTmatFileList,'Fq'));
% MSmatFileList=REFDTmatFileList(contains(REFDTmatFileList,'MS'));


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
    for slotIndex=1:height(WireFitTable)
    x=WireFitTable.DT{slotIndex}.Points(:,1);
    y=WireFitTable.DT{slotIndex}.Points(:,2);
        a1rf=figure(1);
        a1rf.Name=['Br',simuType];     
      
        for timeIdx=4:4
         hold on
        Brvalues = WireFitTable.RtileTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        trisurf(WireFitTable.DT{slotIndex}.ConnectivityList,x,y, abs(Brvalues), abs(Brvalues),'FaceColor','interp')
        end
        a2tf=figure(2);
        a2tf.Name=['Bt',simuType];
        
        for timeIdx=4:4
        hold on
        Btvalues = WireFitTable.TtileTableByElerow{slotIndex}.(sprintf('Step%d', timeIdx));
        trisurf(WireFitTable.DT{slotIndex}.ConnectivityList,x,y, abs(Btvalues), abs(Btvalues),'FaceColor','interp')
        end
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


% ax=tsurf1(1).Parent
% ax2=tsurf2(1).Parent
% ax.Colormap=thermal
% ax2.Colormap=thermal;

% freezeColors(ax);
% freezeColors(colorbar)
% freezeColors(ax2);
% freezeColors(colorbar)

% ax2.f