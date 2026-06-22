%% Table of Contents
% load Mat File (dev_plot3DVectorB_4_SCL_MS_18krpm_case28.m에서 생성)
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
% close all
% load('wireTable_REF_MS_case28.mat');
load('wireTable_SCL_MS_case28.mat')
% load('wireTable_SCL_TS_18krpm_case2.mat');

%% plot config
ztextShiftRatio= 0.90;

linePlotSlotIndex=[8 2]                                    ;         
eleInterval=100                                        ;         
onePeriodSteps  =240                                   ;             
timeShift       =0                                   ;    
sequenceList    =round([3 40 120 151 220 ]*2/3);
timeList        =round([3 40 120 151 220 ])        ; 
timeNameList   =3/2*timeList-3;
ColorList       =colormap("jet");
timeColorList   =ColorList(1:256/len(timeList):256,:);
timeColorList   = [0 0 0;timeColorList]
timeColorList   =num2cell(timeColorList,2);
timeList        = timeList+timeShift;
lineMarkerList={'-','-','-','-'}
SlotList        ={'square','o','^','v','.','diamond','square','o','^','v','.','diamond','square','o','^','v','.','diamond','square','o','^','v','.','diamond'}
SlotFigIndex    =[2*ones(1,4),3*ones(1,4),4*ones(1,4),5*ones(1,4),6*ones(1,4),7*ones(1,4)]
% close all

%% cart2 pol
for slotIndex=1:height(WireTable)
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
figure(5)
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
            'MarkerEdgeColor',timeColorList{timeindex},...
            'MarkerFaceColor','none','Marker',SlotList{slotIndex},...
            'DisplayName',[num2str(timeNameList(timeindex)),'[deg]'])
            hold on
    end
    % % Element ID 추출 알고리즘
     % findClosestPointsToRectangleCorners 함수 호출하여 값을 받아옴
    % [closestPts{slotIndex}, outMostIDs{slotIndex}] = findClosestPointsToRectangleCorners(WireTable(slotIndex,:).elementCentersTable{:});    
    % closestPoints와 OutMostElementIDs에 새 데이터를 추가
    % legend 
    %% 
end
% trimLegendToIndex(len(timeList))
ax=gca;
MSFigure1Legend=      ax.Legend.String;

%% linePlot 
    newlegend=[]
    lineMarkerList={'-','-','-','-'}
    hold on
for slotIndex=1:3:height(WireTable)
    figure(6*(slotIndex))
    tempCenterTable=WireTable(slotIndex,:).elementCentersTable{:};
    outMostIndex=findMatchingRow(tempCenterTable.id,outMostIDs{slotIndex})
    Slot4TTimeArray=[fieldTTimeTable{slotIndex,:}];
    % plot(3*[0:120],Slot4TTimeArray([3:30:end],:))
    degArray=[1.5:360/onePeriodSteps:360];
    plot(degArray,Slot4TTimeArray([outMostIndex],[1+timeShift:onePeriodSteps+timeShift]),'Marker',SlotList{slotIndex},'Color','k','MarkerIndices',sequenceList,'LineStyle',lineMarkerList{slotIndex});
    hold on
    setBElecAngle
    legend
    %%  Element ID N position Str 4 Plot
    eleXCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,1),2)))';
    eleYCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,2),2)))';
    elePos{slotIndex} = cellfun(@(x,y) strcat('[',x,',',y,']'),  eleXCell{slotIndex}, eleYCell{slotIndex}, 'UniformOutput', false);
    eleIdCell{slotIndex}=cellstr(num2str(outMostIDs{slotIndex}))';
    EleStrIdCell{slotIndex} = cellfun(@(x) strcat('MS-FEA',x),elePos{slotIndex}, 'UniformOutput', false);
    newlegend=[ EleStrIdCell{slotIndex}]
    ax=gca;
    ax.Legend.String= [EleStrIdCell{slotIndex} EleStrIdCell{slotIndex}]
    MSFigure2Legend{slotIndex}= newlegend  ;  
    yline(mean(sqrt(Slot4TTimeArray([outMostIndex],:).^2),2),'--.k',EleStrIdCell{slotIndex})
    setlegendBoxShape(4)
end
%% figure 1
tempzLim=0.9*ax.YLim(2);
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
    figure(5)
    scatter3(OutPointtable,'X','Y','Z','Marker','x','MarkerEdgeColor','k');
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
figure(7)
for slotIndex=1:height(WireTable)
    for timeindex=1:len(timeList)
        scatter3((WireTable(slotIndex,:).elementCentersTable{:}(:,'x').Variables),...
            (WireTable(slotIndex,:).elementCentersTable{:}(:,'y').Variables),...
            fieldRTimeTable{slotIndex,timeList(timeindex)},...
            'MarkerEdgeColor',timeColorList{timeindex},...
            'MarkerFaceColor','none','Marker',SlotList{slotIndex},...
            'DisplayName',[num2str(timeNameList(timeindex)),'[deg]'])
            hold on
    end
    legend 
    trimLegendToIndex(len(timeList))
    %% 
end
ax=gca;
MSFigure3Legend=      ax.Legend.String;
%% linePlot 
    newlegend=[]
    hold on
    for slotIndex=1:3:height(WireTable)
        figure(8*(slotIndex))
        tempCenterTable=WireTable(slotIndex,:).elementCentersTable{:};
        outMostIndex=findMatchingRow(tempCenterTable.id,outMostIDs{slotIndex})
        Slot4RTimeArray=[fieldRTimeTable{slotIndex,:}];
        degArray=[1.5:360/onePeriodSteps:360];
        plot(degArray,Slot4RTimeArray([outMostIndex],[1+timeShift:onePeriodSteps+timeShift]),'Marker',SlotList{slotIndex},'Color','k','MarkerIndices',sequenceList,'LineStyle',lineMarkerList{slotIndex});
        hold on
        setBElecAngle

        legend
        %%  Element ID N position Str 4 Plot
        eleXCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,1),2)))';
        eleYCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,2),2)))';
        elePos{slotIndex} = cellfun(@(x,y) strcat('[',x,',',y,']'),  eleXCell{slotIndex}, eleYCell{slotIndex}, 'UniformOutput', false);
        eleIdCell{slotIndex}=cellstr(num2str(outMostIDs{slotIndex}))';
        EleStrIdCell{slotIndex} = cellfun(@(x) strcat('MS-FEA',x),elePos{slotIndex}, 'UniformOutput', false);
        newlegend=[EleStrIdCell{slotIndex}]
        yline(mean(sqrt(Slot4RTimeArray([outMostIndex],:).^2),2),'--.k',EleStrIdCell{slotIndex})
        ax=gca;
        ax.Legend.String=newlegend
        MSFigure4Legend{slotIndex}= newlegend  ; 
        setlegendBoxShape(4)
    end

%%
    tempzLim=0.9*ax.YLim(2);
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
    figure(7)
    scatter3(OutPointtable,'X','Y','Z','Marker','x','MarkerEdgeColor','k');
    hold on 
    text(OutPointArray(:,1),OutPointArray(:,2),...
            zPosArray*ztextShiftRatio,...
            eleIdCellArray)
    trimLegendToIndex(len(timeList))
    setgcaXYcoor
    [RaS,Rview,Rratio]=lockAxisAndView;
