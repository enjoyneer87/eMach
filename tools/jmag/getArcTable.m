function ArcTable=getArcTable(RegionDataTable)


ArcTable=RegionDataTable(strcmp(RegionDataTable.Type,'SketchArc'),:);
if isempty(ArcTable)
    ArcTable=table();
    for RegionIndex=1:height(RegionDataTable)
        if strcmp(RegionDataTable.Type{RegionIndex},'RegionItem')
        sketchList=RegionDataTable.SketchList{RegionIndex};
        RegionArcTable=sketchList{2};
        ArcTable=[ArcTable;RegionArcTable];
        end
    end
end
    % ArcTable=removevars(ArcTable,'Area');

end