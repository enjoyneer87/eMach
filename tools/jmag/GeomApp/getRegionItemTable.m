function AssemRegionTable=getRegionItemTable(refObjTable)

    AssemRegionTable=refObjTable(strcmp(refObjTable.Type,'RegionItem'),:);
% ArcTable=removevars(ArcTable,'Area');

end