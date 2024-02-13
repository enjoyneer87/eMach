function AssemTable=addGeomSetList2AssemTable(AssemTable,geomApp)
    for AssemTableIndex=1:height(AssemTable)
        newGeomSetTable=createJmagGeomSet(AssemTable.GeomSetList{AssemTableIndex},geomApp);
        AssemTable.GeomSetTable{AssemTableIndex}=newGeomSetTable;
    end
end