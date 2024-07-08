function getGeomMagnetizationEdgeSet(RotorAssemRegionTable,geomApp)
RotorRegionTablePerType = detRotorRegionTablePerType(RotorAssemRegionTable);

%% 자석의 edge잡기
for RegionIndex=1:height(RotorRegionTablePerType.MagnetTable)
    slopeTable=[];
    SketchList=RotorRegionTablePerType.MagnetTable.SketchList{RegionIndex};
    LineTable=SketchList{2};
    top4LineTable=LineTable(1:4,:);
    parallelPairs = findParallelLinePairs(top4LineTable);
    parallelLineIndex=parallelPairs(:,1);
    for tempIndex=1:length(parallelPairs(:,1))
        LineIndex=parallelLineIndex(tempIndex);
        startPoint=[top4LineTable.StartVertexTablex(LineIndex),top4LineTable.StartVertexTabley(LineIndex)];
        endPoint=[top4LineTable.EndVertexTablex(LineIndex),top4LineTable.EndVertexTabley(LineIndex)];
        % 
        line(1,1)=top4LineTable.StartVertexTablex(LineIndex);
        line(1,2)=top4LineTable.StartVertexTabley(LineIndex);
        line(2,1)=top4LineTable.EndVertexTablex(LineIndex);
        line(2,2)=top4LineTable.EndVertexTabley(LineIndex);
        % if lineSlope(line)<0
        slopeTable=lineSlope(line);
        % end
     % LineStrc(Lineindex) = {getDirectionalVector(startPoint, endPoint)}
    end
    
    % if isempty(~slopeTable)
    MagnetizeEdgeValue=uniquetol(slopeTable,0.0001);
    MagnetizeEdgeIndex=find(difftol(slopeTable,MagnetizeEdgeValue));
    MagnetizeEdgeTable(RegionIndex).Table=top4LineTable(MagnetizeEdgeIndex(1),:);
    % end
end

    sel=mkSelectionObj(geomApp);
for RegionIndex=1:height(RotorRegionTablePerType.MagnetTable)
    tempEdgeTable=MagnetizeEdgeTable(RegionIndex).Table;
    edgeSet=geomApp.GetDocument().GetAssembly().CreateEdgeSet();
    edgeSet.SetName(RotorRegionTablePerType.MagnetTable.Name{RegionIndex})
    edgeSet.SetProperty("Targets", tempEdgeTable.IdentifierName{:})
    sel.AddReferenceObject(tempEdgeTable.ReferenceObj(:))
end

geomApp.Show

end