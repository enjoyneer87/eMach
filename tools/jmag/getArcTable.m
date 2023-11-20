function ArcTable=getArcTable(RegionDataTable)


ArcTable=RegionDataTable(strcmp(RegionDataTable.Type,'SketchArc'),:);
% ArcTable=removevars(ArcTable,'Area');

end