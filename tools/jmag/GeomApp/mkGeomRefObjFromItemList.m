function RefObjList=mkGeomRefObjFromItemList(ItemList,geomApp)
    geomDocu=geomApp.GetDocument;

for ItemIndex=1:length(ItemList)
    RefObjList{ItemIndex}=geomDocu.CreateReferenceFromItem(ItemList{ItemIndex});
end