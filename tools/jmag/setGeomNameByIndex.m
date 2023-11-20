function setGeomNameByIndex(RegionDataTable,Index2NameImport,app)
sel=mkSelectionObj(app);
geomApp=app.CreateGeometryEditor(0);
% geomView=geomApp.View();
geomDocu=geomApp.GetDocument();

sel.AddReferenceObject(RegionDataTable.ReferenceObj(Index2NameImport))
selCore=geomDocu.GetSelection;
    for ItemNum=1:selCore.Count
        whatis=selCore.Item(ItemNum-1);
        if whatis.IsValid
            % whatis.GetName
            whatis.SetName(RegionDataTable.Name{Index2NameImport})
        end
    end
end