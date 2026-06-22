function rpsubSamplePointLinePlot(WireTable,timeShift)

    load('tempFigConfig.mat');
    allocateStruct2indeVar
    % close all;
%% linePlot 
    newlegend=[];
    lineMarkerList={'-','-','-','-','--','--','--','--','-','-','-','-','--','--','--','--'}    ;
    if nargin<2
    timeShift=0;
    end
for slotIndex=1:2:height(WireTable)
    partName=WireTable.Name{slotIndex};
    partName=strrep(partName,'Stator/','')
    tempCenterTable=WireTable.elementCentersTable{slotIndex};
    outMostIDs{slotIndex}=WireTable.outMostIDs{slotIndex};
    closestPts{slotIndex}=WireTable.closestPts{slotIndex};
    outMostIndex=findMatchingRow(tempCenterTable.id,outMostIDs{slotIndex});
    %% get Table Data
    rTableData=[WireTable.RtimeTableByEleCol{slotIndex,:}];
    tTableData=[WireTable.TtimeTableByEleCol{slotIndex,:}];
    sizeTableData=size(rTableData);
    NumEle   = sizeTableData(2);
    TimeSteps= sizeTableData(1);
    %% 2 Array
    rTimeArrayData=rTableData.Variables'; 
    tTimeArrayData=tTableData.Variables'; 
    degArray=[0+360/(TimeSteps):360/(TimeSteps):360];

    %%legend Name setting
    eleXCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,1),3)))';
    eleYCell{slotIndex}=cellstr(num2str(round(closestPts{slotIndex}(:,2),3)))';
    elePos{slotIndex} = cellfun(@(x,y) strcat('[',x,',',y,']'),  eleXCell{slotIndex}, eleYCell{slotIndex}, 'UniformOutput', false);
    eleIdCell{slotIndex}=cellstr(num2str(outMostIDs{slotIndex}))';
    EleStrIdCell{slotIndex} = cellfun(@(x) strcat(partName,x),elePos{slotIndex}, 'UniformOutput', false);
    newlegend=[ EleStrIdCell{slotIndex}];
    
    %% plot
    figure('Name',[WireTable.Name{slotIndex},'radial'])
    plot(degArray,rTimeArrayData([outMostIndex],[1+timeShift:TimeSteps+timeShift]).^2,'Marker',SlotList{slotIndex},'Color','k','MarkerIndices',sequenceList,'LineStyle',lineMarkerList{slotIndex});
    hold on
    setBElecAngle
    legend
    ax=gca;
    curStr=ax.Legend.String;
    ax.Legend.String= [EleStrIdCell{slotIndex}];
    MSFigure2Legend{slotIndex}= newlegend  ;  
    setlegendBoxShape(4)
    figure('Name',[WireTable.Name{slotIndex},'theta'])
    plot(degArray,tTimeArrayData([outMostIndex],[1+timeShift:TimeSteps+timeShift]).^2,'Marker',SlotList{slotIndex},'Color','k','MarkerIndices',sequenceList,'LineStyle',lineMarkerList{slotIndex});
    setBElecAngle
    legend
    ax=gca;
    curStr=ax.Legend.String;
    ax.Legend.String= [EleStrIdCell{slotIndex}];
    MSFigure2Legend{slotIndex}= newlegend  ;  
    % yline(mean((TimeArrayData([outMostIndex],:).^2),2),'--.k',EleStrIdCell{slotIndex})
    setlegendBoxShape(4)
end

end