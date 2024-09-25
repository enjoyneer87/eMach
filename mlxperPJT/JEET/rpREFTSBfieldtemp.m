%% Table of Contents
% load Mat File (dev_plot3DVectorB_4ExportMVP_Mesh_SHmethod.m에서 생성)
% R theta 로 plot
    % plot config
    % cart2 pol
    % plot
% update Node
% calc HYB Eddy From B
    % Plot HYB P
    % 사각형 그리드로 보간
%  fatami eq 7
%% R theta 로 plot
clear 
close all
% load('wireTable_REF_MS_case28.mat');
load('wireTable_REF_TS_case28.mat');
%% plot config
linePlotSlotIndex=[4 2]                                    ;         
eleInterval=100                                        ;         
onePeriodSteps  =240                                   ;             
timeShift       =240                                  ;             
timeList        =round([3 40 120 151 220 ]*2/3)        ; 
timeNameList   =3/2*timeList-3;
ColorList       =colormap("jet");
timeColorList   =ColorList(1:256/len(timeList):256,:);
timeColorList   = [0 0 0;timeColorList]
timeColorList   =num2cell(timeColorList,2);
timeList        = timeList+timeShift;
SlotList        ={'square','o','^','v','.','diamond','square','o','^','v','.','diamond','square','o','^','v','.','diamond','square','o','^','v','.','diamond'}
SlotFigIndex    =[2*ones(1,4),3*ones(1,4),4*ones(1,4),5*ones(1,4),6*ones(1,4),7*ones(1,4)]
% close all

%% cart2 pol
for slotIndex=1:4
    % BData=WireTable(slotIndex,:);
    for timeindex=1:height(WireTable(slotIndex,:).fieldxTimeTable{:})
        [fieldRTimeTable{slotIndex,timeindex},...
        fieldTTimeTable{slotIndex,timeindex}]=...
        cart2PolVector(WireTable(slotIndex,:).fieldxTimeTable{:}(timeindex,:).Variables',...
               WireTable(slotIndex,:).fieldyTimeTable{:}(timeindex,:).Variables',...
               WireTable(slotIndex,:).elementCentersTable{:}(:,'x').Variables,...
               WireTable(slotIndex,:).elementCentersTable{:}(:,'y').Variables);
    end
end

% MS 는 slot 24개
for slotIndex=1:height(WireTable)
    BData=table2struct(WireTable(slotIndex,:));
    xVar=BData.fieldxTimeTable.Variables;
    yVar=BData.fieldyTimeTable.Variables;
    xPos=BData.elementCentersTable.x';
    yPos=BData.elementCentersTable.y';
    [Fr,Ftheta]=cart2PolVector(xVar,yVar,xPos,yPos);
    Bfield(slotIndex).Br         = Fr     ;
    Bfield(slotIndex).Bthetam    = Ftheta   ;
end

%% plot
% theta
figure(1)
closestPoints=[];
OutMostElementIDs=[];
for slotIndex=1:height(WireTable)
    WireTable(slotIndex,:).elementCentersTable{:}.x=m2mm(WireTable(slotIndex,:).elementCentersTable{:}.x)
    WireTable(slotIndex,:).elementCentersTable{:}.y=m2mm(WireTable(slotIndex,:).elementCentersTable{:}.y)
end

for slotIndex=1:height(WireTable)
    for timeindex=1:len(timeList)
        scatter3((WireTable(slotIndex,:).elementCentersTable{:}(:,'x').Variables),...
            (WireTable(slotIndex,:).elementCentersTable{:}(:,'y').Variables),...
            fieldTTimeTable{slotIndex,timeList(timeindex)},...
            'MarkerEdgeColor','k',...
            'MarkerFaceColor',timeColorList{timeindex},'Marker',SlotList{slotIndex},...
            'DisplayName',[num2str(timeNameList(timeindex)),'[deg]'])
            hold on
    end
    % % Element ID 추출 알고리즘
     % findClosestPointsToRectangleCorners 함수 호출하여 값을 받아옴
    [closestPts{slotIndex}, outMostIDs{slotIndex}] = findClosestPointsToRectangleCorners(WireTable(slotIndex,:).elementCentersTable{:});    
    % closestPoints와 OutMostElementIDs에 새 데이터를 추가
    legend 
    trimLegendToIndex(len(timeList))
    %% 
end

%% linePlot 
    curLegend=[]
    lineMarkerList={'--','-','--','-'}

for slotIndex=1:3:height(WireTable)
    figure(2)
    hold on
    tempCenterTable=WireTable(slotIndex,:).elementCentersTable{:};
    outMostIndex=findMatchingRow(tempCenterTable.id,outMostIDs{slotIndex})
    Slot4TTimeArray=[fieldTTimeTable{slotIndex,:}];
    % plot(3*[0:120],Slot4TTimeArray([3:30:end],:))
    degArray=[1.5:360/onePeriodSteps:360];
    plot(degArray,Slot4TTimeArray([outMostIndex],[1+timeShift:onePeriodSteps+timeShift]),'Marker',SlotList{slotIndex},'Color','r','MarkerIndices',[1:30:len(degArray)],'LineStyle',lineMarkerList{slotIndex});
    hold on
    setBElecAngle
    legend
    ax=gca
    %%  Element ID N position Str 4 Plot
    eleXCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,1),2)))';
    eleYCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,2),2)))';
    elePos{slotIndex} = cellfun(@(x,y) strcat('[',x,',',y,']'),  eleXCell{slotIndex}, eleYCell{slotIndex}, 'UniformOutput', false);
    eleIdCell{slotIndex}=cellstr(num2str(outMostIDs{slotIndex}))';
    EleStrIdCell{slotIndex} = cellfun(@(x) strcat('[xPos,yPos]=',x),elePos{slotIndex}, 'UniformOutput', false);
    curLegend=[curLegend EleStrIdCell{slotIndex}]
    %% 
end
ax.Legend.String=curLegend;
setlegendBoxShape(4)
%% figure 1
tempzLim=1.5*ax.YLim(2);
zPosArray            =[]
closestPointsArray   =[];
OutPointArray        =[];
eleIdCellArray       =[];
% add text  
for slotIndex=1:3:height(WireTable)
    % [closestPts{slotIndex}, outMostIDs{slotIndex}] 
    zPosArray          =[zPosArray;tempzLim*ones(len(closestPts{slotIndex}),1)];
    closestPointsArray =[closestPointsArray; closestPts{slotIndex}];
    eleIdCellArray     =[eleIdCellArray eleIdCell{slotIndex}]
end
%% 2 table
    OutPointArray=[closestPointsArray zPosArray];
    OutPointtable=array2table(OutPointArray);
    OutPointtable.Properties.VariableNames={'X','Y','Z'}
% plot 
    figure(1)
    scatter3(OutPointtable,'X','Y','Z','Marker','*','MarkerEdgeColor','r');
    hold on 
    text(OutPointArray(:,1),OutPointArray(:,2),...
            zPosArray,...
            eleIdCellArray)
    trimLegendToIndex(len(timeList))
    setgcaXYcoor
    [TaS,Tview,Tratio]=lockAxisAndView;
%% 
%% plot
% R
figure(3)
for slotIndex=1:height(WireTable)
    for timeindex=1:len(timeList)
        scatter3((WireTable(slotIndex,:).elementCentersTable{:}(:,'x').Variables),...
            (WireTable(slotIndex,:).elementCentersTable{:}(:,'y').Variables),...
            fieldRTimeTable{slotIndex,timeList(timeindex)},...
            'MarkerEdgeColor','k',...
            'MarkerFaceColor',timeColorList{timeindex},'Marker',SlotList{slotIndex},...
            'DisplayName',[num2str(timeNameList(timeindex)),'[deg]'])
            hold on
    end
    legend 
    trimLegendToIndex(len(timeList))
    %% 
end
%% linePlot 
    curLegend=[]
    lineMarkerList={'--','-','--','-'}
figure(4)
    hold on
    for slotIndex=1:3:height(WireTable)
        tempCenterTable=WireTable(slotIndex,:).elementCentersTable{:};
        outMostIndex=findMatchingRow(tempCenterTable.id,outMostIDs{slotIndex})
        Slot4RTimeArray=[fieldRTimeTable{slotIndex,:}];
        degArray=[1.5:360/onePeriodSteps:360];
        plot(degArray,Slot4RTimeArray([outMostIndex],[1+timeShift:onePeriodSteps+timeShift]),'Marker',SlotList{slotIndex},'Color','r','MarkerIndices',[1:30:len(degArray)],'LineStyle',lineMarkerList{slotIndex});
        hold on
        setBElecAngle
        legend
        %%  Element ID N position Str 4 Plot
        eleXCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,1),2)))';
        eleYCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,2),2)))';
        elePos{slotIndex} = cellfun(@(x,y) strcat('[',x,',',y,']'),  eleXCell{slotIndex}, eleYCell{slotIndex}, 'UniformOutput', false);
        eleIdCell{slotIndex}=cellstr(num2str(outMostIDs{slotIndex}))';
        EleStrIdCell{slotIndex} = cellfun(@(x) strcat('[xPos,yPos]=',x),elePos{slotIndex}, 'UniformOutput', false);
        curLegend=[curLegend EleStrIdCell{slotIndex}]
        %% 
    end
    ax=gca;
    ax.Legend.String=curLegend;
    setlegendBoxShape(4)
%%
    tempzLim=1.5*ax.YLim(2);
    zPosArray            =[];
    closestPointsArray   =[];
    OutPointArray        =[];
    eleIdCellArray       =[];
    % add text  
    for slotIndex=1:3:height(WireTable)
        % [closestPts{slotIndex}, outMostIDs{slotIndex}] 
        zPosArray          =[zPosArray;tempzLim*ones(len(closestPts{slotIndex}),1)];
        closestPointsArray =[closestPointsArray; closestPts{slotIndex}];
        eleIdCellArray     =[eleIdCellArray eleIdCell{slotIndex}];
    end
%% 2 table
    OutPointArray=[closestPointsArray zPosArray];
    OutPointtable=array2table(OutPointArray);
    OutPointtable.Properties.VariableNames={'X','Y','Z'}
% plot 
    figure(3)
    scatter3(OutPointtable,'X','Y','Z','Marker','*','MarkerEdgeColor','k');
    hold on 
    text(OutPointArray(:,1),OutPointArray(:,2),...
            zPosArray,...
            eleIdCellArray)
    trimLegendToIndex(len(timeList))
    setgcaXYcoor
    [RaS,Rview,Rratio]=lockAxisAndView;


%% Mesh Plot
load('REF_TS_18krpm_case28_Mesh.mat')
 figure(1)
plotJMAGMesh(TSMesh)
ax=gca;
restoreView(ax, TaS,Tview,Tratio)
legend
figure(3)
plotJMAGMesh(TSMesh)
ax=gca;
restoreView(ax,RaS,Rview,Rratio)
legend
% 
% 
% %%
% figure(2)
% Slot4TTimeArray=[fieldTTimeTable{linePlotSlotIndex,:}];
% % plot(3*[0:120],Slot4TTimeArray([3:30:end],:))
% plot([0:360/onePeriodSteps:360],Slot4TTimeArray([3:eleInterval:end],[1+timeShift-1:onePeriodSteps+timeShift]),'r');
% % % [TC] periodicity
% % plot([1:41],-Slot4TTimeArray([3:30:end],[1:41]),'r')
% % plot([1:41],-Slot4TTimeArray([3:30:end],[41:81]),'Color','b','LineStyle','--')
% 
% % R
% figure(3)
% for slotIndex=1:4
%     BData=WireTable(slotIndex,:);
%     for timeindex=1:len(timeList)
%         scatter3(m2mm(BData.elementCentersTable{:}(:,'x').Variables),...
%             m2mm(BData.elementCentersTable{:}(:,'y').Variables),...
%             fieldRTimeTable{slotIndex,timeList(timeindex)},...
%             'MarkerEdgeColor',timeColorList{timeindex},...
%             'MarkerFaceColor','none','Marker',SlotList{slotIndex},...
%             'DisplayName',[num2str(3*timeList(timeindex)-3),'[deg]'])
%             hold on
%     end
% end
% legend
% trimLegendToIndex(len(timeList))
% eleInterval=100
% figure(4)
% Slot4RTimeArray=[fieldRTimeTable{4,:}]
% % plot(3*[0:120],Slot4TTimeArray([3:30:end],:))
% plot(3*[0:120],Slot4RTimeArray([1:eleInterval:end],[1:121]),'k')
% legend
% ax=gca
% eleIdCell=cellstr(num2str(BData.elementCentersTable{:}.id(1:eleInterval:end)))'
% % 기존 셀 배열 eleIdCell에 일괄적으로 "elementID" 추가
% EleStrIdCell = cellfun(@(x) strcat('Element:',x), eleIdCell, 'UniformOutput', false);
% ax.Legend.String=EleStrIdCell
% % add text 
% elementCentersTable=BData.elementCentersTable{:}
% 
% figure(3)
% for eleIndex=1:len(eleIdCell)
%     scatter3(m2mm(elementCentersTable(elementCentersTable.id==str2num(eleIdCell{eleIndex}),'x').Variables),...
%             m2mm(elementCentersTable(elementCentersTable.id==str2num(eleIdCell{eleIndex}),'y').Variables),...
%             -0.1,...
%             'k','Marker','x')
%    hold on 
%     text(m2mm(elementCentersTable(elementCentersTable.id==str2num(eleIdCell{eleIndex}),'x').Variables),...
%             m2mm(elementCentersTable(elementCentersTable.id==str2num(eleIdCell{eleIndex}),'y').Variables),...
%             -0.15,...
%             eleIdCell{eleIndex})
% end
% trimLegendToIndex(len(timeList))

%% [TC] deluaytri

%% grid Interp
% D:\KangDH\Emlab_emach\mlxperPJT\JEET\devFieldGridInterp.m