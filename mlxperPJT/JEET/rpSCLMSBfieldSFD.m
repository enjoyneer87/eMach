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
% load('wireTable_SCL_TS_18krpm_case28.mat')
load('wireTable_SCL_MS_case1.mat');

%% plot config
tempFigConfig.ztextShiftRatio= 0.90;
tempFigConfig.linePlotSlotIndex=[4 2]                                    ;         
tempFigConfig.eleInterval=100                                        ;         
tempFigConfig.onePeriodSteps  =240                                   ;             
tempFigConfig.timeShift       =0                                   ;    
% tempFigConfig.sequenceList    =round([3 40 120 151 220 ]*2/3);
% tempFigConfig.timeList        =round([3 40 120 151 220 ])        ; 
tempFigConfig.sequenceList    =round([3:30:360]*2/3);
tempFigConfig.timeList        =round([3:20:360]*2/3)        ; 
tempFigConfig.timeNameList   =3/2*tempFigConfig.timeList-3;
tempFigConfig.ColorList       =colormap("jet");
tempFigConfig.timeColorList   =tempFigConfig.ColorList(1:256/len(tempFigConfig.timeList):256,:);
tempFigConfig.timeColorList   = [0 0 0;tempFigConfig.timeColorList]
tempFigConfig.timeColorList   =num2cell(tempFigConfig.timeColorList,2);
tempFigConfig.timeList        = tempFigConfig.timeList+tempFigConfig.timeShift;
tempFigConfig.lineMarkerList={'-','-','-','-'}
tempFigConfig.SlotList        ={'square','o','^','v','.','diamond','square','o','^','v','.','diamond','square','o','^','v','.','diamond','square','o','^','v','.','diamond'}
tempFigConfig.SlotFigIndex    =[2*ones(1,4),3*ones(1,4),4*ones(1,4),5*ones(1,4),6*ones(1,4),7*ones(1,4)]
save('tempFigConfig.mat','tempFigConfig')
% close all

        timeList=[1:20:240]

%% plot
% theta
figure(5)
closestPoints=[];
OutMostElementIDs=[];
allocateStruct2indeVar
slotIndex=12
clear plotTable
plotTable=[]
for slotIndex=1:16
    plotTable=[plotTable; WireTable.TtileTableByElerow{slotIndex}]


    for timeindex=1:len(timeList)
        TTabvar=WireTable.TtimeTableByEleCol{slotIndex}.Variables;
        timeList=[1:20:240]
        for  timeindex=1:len(timeList)
        timeStep=    timeList(timeindex)
        scatter3(plotTable,'x','y',StepsName{timeStep},'MarkerEdgeColor',timeColorList{timeindex})
        hold on
        end
        % plot(WireTable.tileTableByElerow{slotIndex}.Step173)
        % ...
        %     'MarkerEdgeColor',timeColorList{timeindex},...
        %     'MarkerFaceColor','none','Marker',SlotList{slotIndex},...
        %     'DisplayName',[num2str(timeNameList(timeindex)),'[deg]'])
        %     hold on
    end
    legend 
    %% 
end
trimLegendToIndex(len(timeList))
ax=gca;
MSFigure1Legend=      ax.Legend.String;


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
% figure2

rpsubSamplePointLinePlot(WireTable)
sourceFig = findobj('Type', 'figure');
figureNameList =flipud({sourceFig.Name}')
Wire3ListR=(contains(figureNameList,'Wire3')&contains(figureNameList,'radial'))&(contains(figureNameList,'Slot1')|contains(figureNameList,'Slot3'))
Wire3Listt=contains(figureNameList,'Wire3')&contains(figureNameList,'theta')
Wire1ListR=contains(figureNameList,'Wire1')&contains(figureNameList,'radial')
Wire1Listt=contains(figureNameList,'Wire1')&contains(figureNameList,'theta')

targetFigs1=mergeFigures(find(Wire1ListR))
view(2)
targetFigs2=mergeFigures(find(Wire3ListR))
view(2)
targetFigs3=mergeFigures(find(Wire1Listt))
view(2)
targetFigs4=mergeFigures(find(Wire3Listt))
view(2)

fig2del=[targetFigs1 targetFigs2 targetFigs3 targetFigs4]

for figIdx=1:len(fig2del)
close(fig2del(figIdx))
end
 
%% 2 table
%     OutPointArray=[closestPointsArray zPosArray];
%     OutPointtable=array2table(OutPointArray);
%     OutPointtable.Properties.VariableNames={'X','Y','Z'}
% % plot 
%     figure(5)
%     scatter3(OutPointtable,'X','Y','Z','Marker','x','MarkerEdgeColor','k');
%     hold on 
%     text(OutPointArray(:,1),OutPointArray(:,2),...
%             zPosArray*ztextShiftRatio,...
%             eleIdCellArray)
%     trimLegendToIndex(len(timeList))
%     setgcaXYcoor
%     [TaS,Tview,Tratio]=lockAxisAndView;
%% 
%% plot
% R
figure(7)
for slotIndex=1:height(WireTable)
    for timeindex=1:len(timeList)
        RTabvar=WireTable.RtimeTableByEleCol{slotIndex}.Variables;
        scatter3((WireTable(slotIndex,:).elementCentersTable{:}(:,'x').Variables),...
            (WireTable(slotIndex,:).elementCentersTable{:}(:,'y').Variables),...
            [RTabvar(timeindex,:).^2],...
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
        plot(degArray,Slot4RTimeArray([outMostIndex],[1+timeShift:onePeriodSteps+timeShift]).^2,'Marker',SlotList{slotIndex},'Color','k','MarkerIndices',sequenceList,'LineStyle',lineMarkerList{slotIndex});
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
        yline(mean((Slot4RTimeArray([outMostIndex],:).^2),2),'--.k',EleStrIdCell{slotIndex})
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
% % plot 
%     figure(7)
%     scatter3(OutPointtable,'X','Y','Z','Marker','x','MarkerEdgeColor','k');
%     hold on 
%     text(OutPointArray(:,1),OutPointArray(:,2),...
%             zPosArray*ztextShiftRatio,...
%             eleIdCellArray)
%     trimLegendToIndex(len(timeList))
%     setgcaXYcoor
%     [RaS,Rview,Rratio]=lockAxisAndView;
