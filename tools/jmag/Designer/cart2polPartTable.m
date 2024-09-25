function WireTable=cart2polPartTable(WireTable)
    WireTable.RtimeTableByEleCol=WireTable.fieldyTimeTable;
    WireTable.TtimeTableByEleCol=WireTable.fieldyTimeTable;
for slotIndex=1:height(WireTable)
    Fx=WireTable.fieldxTimeTable{slotIndex}.Variables;
    Fy=WireTable.fieldxTimeTable{slotIndex}.Variables;
    x=WireTable.elementCentersTable{slotIndex}.x;
    y=WireTable.elementCentersTable{slotIndex}.y;
    % scatter3(x,y,Fy(1,:))
    [tempR,tempTetha]=cart2PolVector(Fx,Fy,x,y);
    WireTable.RtimeTableByEleCol{slotIndex}.Variables=tempR;
    WireTable.RtimeTableByEleCol{slotIndex}.Variables=tempTetha;    
    %% addtional 
    [WireTable.closestPts{slotIndex}, WireTable.outMostIDs{slotIndex}] = findClosestPointsToRectangleCorners(WireTable.elementCentersTable{slotIndex});    
    %% Add Elerow Table
    WireTable.TtileTableByElerow{slotIndex}=rows2vars(WireTable.TtimeTableByEleCol{slotIndex});
    WireTable.TtileTableByElerow{slotIndex}.OriginalVariableNames=[];
    varNames=WireTable.TtileTableByElerow{slotIndex}.Properties.VariableNames;
    StepsName=cellfun(@(x) strrep(x,'Var','Step'),varNames,'UniformOutput',false);
    WireTable.TtileTableByElerow{slotIndex}.Properties.VariableNames=StepsName;
    WireTable.TtileTableByElerow{slotIndex}=[WireTable.elementCentersTable{slotIndex} WireTable.TtileTableByElerow{slotIndex} ];
    %%
    WireTable.RtileTableByElerow{slotIndex}=rows2vars(WireTable.RtimeTableByEleCol{slotIndex});
    WireTable.RtileTableByElerow{slotIndex}.OriginalVariableNames=[];
    varNames=WireTable.RtileTableByElerow{slotIndex}.Properties.VariableNames;
    StepsName=cellfun(@(x) strrep(x,'Var','Step'),varNames,'UniformOutput',false);
    WireTable.RtileTableByElerow{slotIndex}.Properties.VariableNames=StepsName;
    WireTable.RtileTableByElerow{slotIndex}=[WireTable.elementCentersTable{slotIndex} WireTable.RtileTableByElerow{slotIndex} ];
end


end