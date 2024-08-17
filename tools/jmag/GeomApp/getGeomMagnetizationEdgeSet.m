function getGeomMagnetizationEdgeSet(RotorAssemRegionTable,geomApp)

geomDocu  = geomApp.GetDocument;
geomAssem= geomDocu.GetAssembly;
NumEdgeSet=geomDocu.NumEdgeSet;

RotorRegionTablePerType = detRotorRegionTablePerType(RotorAssemRegionTable);
MagnetTable  =RotorRegionTablePerType.MagnetTable;
%% Mirror 할꺼라서 반절씩만 Set만들기
uniqueArea=uniquetol(MagnetTable.Area,0.001);
for UniqueIndex=1:length(uniqueArea)
isSame=find(difftol(MagnetTable.Area,uniqueArea(UniqueIndex),0.001));
theOnlyCell(UniqueIndex)=isSame(1);
end
NonMirrorMagnetTable =MagnetTable(theOnlyCell,:);
%% 만들어놓은 Set 중복제거
if ~NumEdgeSet==0
    for ItemIndex=1:NumEdgeSet
        EdgeSet=geomAssem.GetGeometrySet(int32(ItemIndex-1));
        if EdgeSet.IsValid
            madeEdgeSetList{ItemIndex}=EdgeSet.GetName;
            NonMirrorMagnetTable=NonMirrorMagnetTable(~contains(NonMirrorMagnetTable.sketchItemName, madeEdgeSetList{ItemIndex}),:);
        end
    end
    MagnetTable=NonMirrorMagnetTable;
elseif NumEdgeSet==0
    MagnetTable          =NonMirrorMagnetTable;
end


%% 자석의 edge잡기
for RegionIndex=1:height(MagnetTable)
    slopeTable=[];
    SketchList=MagnetTable.SketchList{RegionIndex};
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

%% set 만들기
    % sel=mkSelectionObj(geomApp);
for RegionIndex=1:height(MagnetTable)
    tempEdgeTable=MagnetizeEdgeTable(RegionIndex).Table;
    edgeSet=geomApp.GetDocument().GetAssembly().CreateEdgeSet();
    edgeSet.SetName(MagnetTable.Name{RegionIndex})
    edgeSet.SetProperty("Targets", tempEdgeTable.IdentifierName{:})
    % sel.AddReferenceObject(tempEdgeTable.ReferenceObj(:))
end

geomApp.Show

end