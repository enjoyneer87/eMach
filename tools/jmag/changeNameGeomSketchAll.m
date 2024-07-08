function RegionDataTable=changeNameGeomSketchAll(RegionDataTable,geomApp)
% RegionDataTable=StatorAssemRegionTable
    for Index4ChangeObject=height(RegionDataTable):-1:1
       setGeomNameByIndex(RegionDataTable,Index4ChangeObject,geomApp)
          % setGeomNameByIndex(RegionDataTable,Index4ChangeObject,geomApp)
       RegionDataTable=getGeomNameByIndex(RegionDataTable,Index4ChangeObject,geomApp);
    end
end