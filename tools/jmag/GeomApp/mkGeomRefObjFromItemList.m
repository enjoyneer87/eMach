function RefObjList=mkGeomRefObjFromItemList(ItemList,geomApp)
    geomDocu=geomApp.GetDocument;

for ItemIndex=1:length(ItemList)
    if iscell(ItemList)
       RefObjList{ItemIndex}=geomDocu.CreateReferenceFromItem(ItemList{ItemIndex});
    else
       RefObjList{ItemIndex}=geomDocu.CreateReferenceFromItem(ItemList(ItemIndex)); 
    end
end