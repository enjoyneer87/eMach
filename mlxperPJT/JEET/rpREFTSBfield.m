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
ztextShiftRatio= 1.10;
linePlotSlotIndex=[4 2]                                    ;         
eleInterval=100                                        ;         
onePeriodSteps  =240                                   ;             
timeShift       =240                                  ;  
sequenceList    =round([3 40 120 151 220 ]*2/3);
timeList        =round(sequenceList)        ; 
timeNameList   =3/2*timeList-3;
ColorList       =colormap("jet");
timeColorList   =ColorList(1:256/len(timeList):256,:);
timeColorList   = [0 0 0;timeColorList]
timeColorList   =num2cell(timeColorList,2);
timeList        = timeList+timeShift;
lineMarkerList={'--','--','--','--'}
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
ax=gca;
TSfigure1Legned=ax.Legend.String;

%% linePlot 
    newLegend=[]
    hold on
for slotIndex=1:3:height(WireTable)
    figure(2*10*slotIndex)
    tempCenterTable=WireTable(slotIndex,:).elementCentersTable{:};
    outMostIndex=findMatchingRow(tempCenterTable.id,outMostIDs{slotIndex})
    Slot4TTimeArray=[fieldTTimeTable{slotIndex,:}];
    % plot(3*[0:120],Slot4TTimeArray([3:30:end],:))
    degArray=[1.5:360/onePeriodSteps:360];
    plot(degArray,Slot4TTimeArray([outMostIndex],[1+timeShift:onePeriodSteps+timeShift]),'Marker',SlotList{slotIndex},'Color','r','MarkerIndices',sequenceList,'LineStyle',lineMarkerList{slotIndex});
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
    newLegend=[EleStrIdCell{slotIndex}]
    ax=gca;
    ax.Legend.String=newLegend;
    TSfigure2Legned{slotIndex}=ax.Legend.String;
    setlegendBoxShape(2)
end

%% figure 1
tempzLim=ax.YLim(2)*0.9;
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
            zPosArray*ztextShiftRatio,...
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
ax=gca;
TSfigure3Legned=ax.Legend.String;
%% linePlot 
    newLegend=[]
    hold on
    for slotIndex=1:3:height(WireTable)
        figure(4*slotIndex)
        tempCenterTable=WireTable(slotIndex,:).elementCentersTable{:};
        outMostIndex=findMatchingRow(tempCenterTable.id,outMostIDs{slotIndex})
        Slot4RTimeArray=[fieldRTimeTable{slotIndex,:}];
        degArray=[1.5:360/onePeriodSteps:360];
        plot(degArray,Slot4RTimeArray([outMostIndex],[1+timeShift:onePeriodSteps+timeShift]),'Marker',SlotList{slotIndex},'Color','r','MarkerIndices',sequenceList,'LineStyle',lineMarkerList{slotIndex});
        hold on
        setBElecAngle
        legend
        %%  Element ID N position Str 4 Plot
        eleXCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,1),2)))';
        eleYCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,2),2)))';
        elePos{slotIndex} = cellfun(@(x,y) strcat('[',x,',',y,']'),  eleXCell{slotIndex}, eleYCell{slotIndex}, 'UniformOutput', false);
        eleIdCell{slotIndex}=cellstr(num2str(outMostIDs{slotIndex}))';
        EleStrIdCell{slotIndex} = cellfun(@(x) strcat('[xPos,yPos]=',x),elePos{slotIndex}, 'UniformOutput', false);
        newLegend=[EleStrIdCell{slotIndex}]
        ax=gca;
        ax.Legend.String=newLegend;
        TSfigure4Legned{slotIndex}=ax.Legend.String;
        setlegendBoxShape(2)
    end

%%
    tempzLim=ax.YLim(2)*0.9;
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
    scatter3(OutPointtable,'X','Y','Z','Marker','*','MarkerEdgeColor','r');
    hold on 
    text(OutPointArray(:,1),OutPointArray(:,2),...
            zPosArray*ztextShiftRatio,...
            eleIdCellArray)
    trimLegendToIndex(len(timeList))
    setgcaXYcoor
    [RaS,Rview,Rratio]=lockAxisAndView;

TSlegendNames.TSfigure4Legned      =TSfigure4Legned
TSlegendNames.TSfigure1Legned      =TSfigure1Legned
TSlegendNames.TSfigure2Legned      =TSfigure2Legned
TSlegendNames.TSfigure3Legned      =TSfigure3Legned
save("TSLegendNameList.mat",'TSlegendNames')
