%% Table of Contents
% load Mat File (dev_plot3DVectorB_4_SCL_TS_18krpm_case28.m에서 생성)
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
% load('wireTable_SCL_TS_18krpm_case28.mat');
% load('wireTable_SCL_TS_18krpm_case2.mat');
load('wireTable_SCL_TS_18krpm_case28.mat');

%% plot config

%% plot config
tempFigConfig.ztextShiftRatio= 0.90;
tempFigConfig.linePlotSlotIndex=[4 2]                                    ;         
tempFigConfig.eleInterval=100                                        ;         
tempFigConfig.onePeriodSteps  =240                                   ;             
tempFigConfig.timeShift       =240                                  ;    
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
close all

timeList=tempFigConfig.timeList ;
%% plot
% theta
figure(1)
TplotTable=[]
RplotTable=[]
AbsPlotTable=[];
for slotIndex=1:16
%T
TValueTable=WireTable.TtileTableByElerow{slotIndex};
StepTimeTable=WireTable.TtileTableByElerow{1}.Properties.VariableNames;
StepsName=StepTimeTable(contains(StepTimeTable,'Step'));
TSFDTable=TValueTable(:,StepsName).^2;
TValueTable(:,contains(StepTimeTable,'Step'))=TSFDTable;
TplotTable=[TplotTable; TValueTable];
%% R
RValueTable=WireTable.RtileTableByElerow{slotIndex};
RSFDTable=RValueTable(:,StepsName).^2;
RValueTable(:,contains(StepTimeTable,'Step'))=RSFDTable;
RplotTable=[RplotTable; RValueTable];
%% Abs 
AbsPlotTable=[AbsPlotTable;sqrt(RSFDTable+TSFDTable)];
end
AbsPlotTable=addvars(AbsPlotTable,RplotTable.x,RplotTable.y,'NewVariableNames',{'x','y'})

closestPoints=[];
OutMostElementIDs=[];
allocateStruct2indeVar
close all
for  timeindex=1:len(timeList)
    timeStep=timeList(timeindex);
    figure(1)
    scatter3(TplotTable,'x','y',StepsName,'MarkerEdgeColor',timeColorList{timeindex})
    hold on
    figure(2)
    scatter3(RplotTable,'x','y',StepsName,'MarkerEdgeColor',timeColorList{timeindex})
    hold on
    figure(3)
    scatter3(AbsPlotTable,'x','y',StepsName,'MarkerEdgeColor',timeColorList{timeindex})
    hold on
end
% end
    % plot(WireTable.tileTableByElerow{slotIndex}.Step173)
    % ...
    %     'MarkerEdgeColor',timeColorList{timeindex},...
    %     'MarkerFaceColor','none','Marker',SlotList{slotIndex},...
    %     'DisplayName',[num2str(timeNameList(timeindex)),'[deg]'])
    %     hold on


ax=gca;
TSfigure1Legned=ax.Legend.String;

%% linePlot 
    newLegend=[]
    lineMarkerList={'--','--','--','--'}
    hold on
for slotIndex=1:3:height(WireTable)
    figure(2*10*slotIndex)
    tempCenterTable=WireTable(slotIndex,:).elementCentersTable{:};
    outMostIndex=findMatchingRow(tempCenterTable.id,outMostIDs{slotIndex})
    Slot4TTimeArray=[fieldTTimeTable{slotIndex,:}];
    % plot(3*[0:120],Slot4TTimeArray([3:30:end],:))
    degArray=[1.5:360/onePeriodSteps:360];
    plot(degArray,Slot4TTimeArray([outMostIndex],[1+timeShift:onePeriodSteps+timeShift]).^2,'Marker',SlotList{slotIndex},'Color','r','MarkerIndices',sequenceList,'LineStyle',lineMarkerList{slotIndex});
    hold on
    setBElecAngle
    legend
    %%  Element ID N position Str 4 Plot
    eleXCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,1),2)))';
    eleYCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,2),2)))';
    elePos{slotIndex} = cellfun(@(x,y) strcat('[',x,',',y,']'),  eleXCell{slotIndex}, eleYCell{slotIndex}, 'UniformOutput', false);
    eleIdCell{slotIndex}=cellstr(num2str(outMostIDs{slotIndex}))';
    EleStrIdCell{slotIndex} = cellfun(@(x) strcat('TS-FEA',x),elePos{slotIndex}, 'UniformOutput', false);
    % newLegend=[newLegend EleStrIdCell{slotIndex}]
    yline(mean((Slot4TTimeArray([outMostIndex],:).^2),2),'-.r',EleStrIdCell{slotIndex})
    ax=gca;
    ax.Legend.String=EleStrIdCell{slotIndex};
    TSfigure2Legned{slotIndex}=ax.Legend.String;
    setlegendBoxShape(4)
end
load('SCL_TS_18krpm_case28_Mesh.mat')
pdeplot(SCL_TSMesh.model.Mesh)
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
    % % scatter3(OutPointtable,'X','Y','Z','Marker','*','MarkerEdgeColor','r');
    % hold on 
    % text(OutPointArray(:,1),OutPointArray(:,2),...
    %         zPosArray*ztextShiftRatio,...
    %         eleIdCellArray)
    % trimLegendToIndex(len(timeList))
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
            fieldRTimeTable{slotIndex,timeList(timeindex)}.^2,...
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
    lineMarkerList={'--','--','--','--'}
    hold on
    for slotIndex=1:3:height(WireTable)
        figure(4*slotIndex)
        tempCenterTable=WireTable(slotIndex,:).elementCentersTable{:};
        outMostIndex=findMatchingRow(tempCenterTable.id,outMostIDs{slotIndex})
        Slot4RTimeArray=[fieldRTimeTable{slotIndex,:}];
        degArray=[1.5:360/onePeriodSteps:360];
        plot(degArray,Slot4RTimeArray([outMostIndex],[1+timeShift:onePeriodSteps+timeShift]).^2,'Marker',SlotList{slotIndex},'Color','r','MarkerIndices',sequenceList,'LineStyle',lineMarkerList{slotIndex});
        hold on
        setBElecAngle
        legend
        %%  Element ID N position Str 4 Plot
        eleXCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,1),2)))';
        eleYCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,2),2)))';
        elePos{slotIndex} = cellfun(@(x,y) strcat('[',x,',',y,']'),  eleXCell{slotIndex}, eleYCell{slotIndex}, 'UniformOutput', false);
        eleIdCell{slotIndex}=cellstr(num2str(outMostIDs{slotIndex}))';
        EleStrIdCell{slotIndex} = cellfun(@(x) strcat('TS-FEA',x),elePos{slotIndex}, 'UniformOutput', false);
        % newLegend=[newLegend EleStrIdCell{slotIndex}]
        yline(mean((Slot4RTimeArray([outMostIndex],:).^2),2),'-.r',EleStrIdCell{slotIndex})
        ax=gca;
        ax.Legend.String=EleStrIdCell{slotIndex};

        TSfigure4Legned{slotIndex}=ax.Legend.String;
        %% 
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
    % % scatter3(OutPointtable,'X','Y','Z','Marker','*','MarkerEdgeColor','r');
    % hold on 
    % text(OutPointArray(:,1),OutPointArray(:,2),...
    %         zPosArray*ztextShiftRatio,...
    %         eleIdCellArray)
    % trimLegendToIndex(len(timeList))
    setgcaXYcoor
    % [RaS,Rview,Rratio]=lockAxisAndView;
   %  ax=gca
   % Ras= TaS
   %    Ras(end)= TaS(end)/4
% restoreView(ax,Ras,Tview,[2 1.1 0.002/4])
TSlegendNames.TSfigure4Legned      =TSfigure4Legned
TSlegendNames.TSfigure1Legned      =TSfigure1Legned
TSlegendNames.TSfigure2Legned      =TSfigure2Legned
TSlegendNames.TSfigure3Legned      =TSfigure3Legned
save("TSLegendNameList.mat",'TSlegendNames')

%%

    % yline(,'Marker',SlotList{slotIndex},'Color','r','MarkerIndices',sequenceList,'LineStyle',lineMarkerList{slotIndex});
