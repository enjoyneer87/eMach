function WireTable=cart2polPartTable(WireTable)
    WireTable.TtimeTableByEleCol=WireTable.fieldyTimeTable;
    WireTable.RtimeTableByEleCol=WireTable.fieldxTimeTable;
for slotIndex=1:height(WireTable)
    Fx=WireTable.fieldxTimeTable{slotIndex}.Variables;
    Fy=WireTable.fieldyTimeTable{slotIndex}.Variables;
    if contains(WireTable.fieldxTimeTable{slotIndex}.Properties.Description,'Element','IgnoreCase',true)
        x=WireTable.elementCentersTable{slotIndex}.x;
        y=WireTable.elementCentersTable{slotIndex}.y;
        % scatter3(x,y,Fy(1,:))
    
        %% Vector 
        [tempR,tempTetha]=cart2PolVector(Fx,Fy,x,y);

        WireTable.TtimeTableByElerow{slotIndex}=rows2vars(WireTable.TtimeTableByEleCol{slotIndex});

        WireTable.RtimeTableByElerow{slotIndex}=rows2vars(WireTable.RtimeTableByEleCol{slotIndex});
        %% addtional 
        [WireTable.closestPts{slotIndex}, WireTable.outMostIDs{slotIndex}] = findClosestPointsToRectangleCorners(WireTable.elementCentersTable{slotIndex});    
        %% Add Elerow Table Theta
        WireTable.TtimeTableByElerow{slotIndex}.Properties.RowNames=WireTable.TtimeTableByElerow{slotIndex}.OriginalVariableNames;
        WireTable.TtimeTableByElerow{slotIndex}.OriginalVariableNames=[];
        varNames=WireTable.TtimeTableByElerow{slotIndex}.Properties.VariableNames;
        StepsName=cellfun(@(x) strrep(x,'Var','Step'),varNames,'UniformOutput',false);
        WireTable.TtimeTableByElerow{slotIndex}.Properties.VariableNames=StepsName;
        WireTable.TtimeTableByElerow{slotIndex}.Variables=tempTetha;    
        WireTable.TtimeTableByElerow{slotIndex}=[WireTable.elementCentersTable{slotIndex} WireTable.TtimeTableByElerow{slotIndex} ];
         %% RtileTableByElerow
        WireTable.RtimeTableByElerow{slotIndex}.Properties.RowNames=WireTable.RtimeTableByElerow{slotIndex}.OriginalVariableNames;
        WireTable.RtimeTableByElerow{slotIndex}.OriginalVariableNames=[];
        varNames=WireTable.RtimeTableByElerow{slotIndex}.Properties.VariableNames;
        StepsName=cellfun(@(x) strrep(x,'Var','Step'),varNames,'UniformOutput',false);
        WireTable.RtimeTableByElerow{slotIndex}.Properties.VariableNames=StepsName;
        WireTable.RtimeTableByElerow{slotIndex}.Variables=tempR;
        WireTable.RtimeTableByElerow{slotIndex}=[WireTable.elementCentersTable{slotIndex} WireTable.RtimeTableByElerow{slotIndex} ];

    end
end


end