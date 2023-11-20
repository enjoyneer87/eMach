function changeNameGeomSketchWithList(RegionDataTable,list4Change,app)
    for Index4ChangeObject=1:length(list4Change)
        Index2NameImport=list4Change(Index4ChangeObject);
         setGeomNameByIndex(RegionDataTable,Index2NameImport,app);
    end
end