function AssemItemtable=addRefObj2AssemTable(AssemItemtable,geomApp)
%% RefObj
if isvarofTable(AssemItemtable,'sketchItemObj')
RefObjList=mkGeomRefObjFromItemList(AssemItemtable.sketchItemObj,geomApp);
elseif isvarofTable(AssemItemtable,'AssemItem')
RefObjList=mkGeomRefObjFromItemList(AssemItemtable.AssemItem,geomApp);
end

RefObjIdentifierList=getRefObjIdentifierName(RefObjList);

%% 2 Table
AssemItemtable.IdentifierName   =RefObjIdentifierList;
AssemItemtable.ReferenceObj     =RefObjList';

end