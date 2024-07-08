function IdentifierList=getRefObjIdentifierName(RefObjList)
    
IdentifierList=cell(length(RefObjList),1);
for RefObjIndex=1:length(RefObjList)
    IdentifierList{RefObjIndex}=RefObjList{RefObjIndex}.GetIdentifier;
end

end