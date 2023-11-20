function changeNameGeomSketchAll(RegionDataTable,app)
    for Index4ChangeObject=1:height(RegionDataTable)
       setGeomNameByIndex(RegionDataTable,Index4ChangeObject,app)
    end
end