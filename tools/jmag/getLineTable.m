function sketchLineTable=getLineTable(RegionDataTable)


sketchLineTable=RegionDataTable(strcmp(RegionDataTable.Type,'SketchLine'),:);
% ArcTable=removevars(ArcTable,'Area');

end