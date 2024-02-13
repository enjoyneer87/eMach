function SubItemObj=getGeomAppSolidPartItems(PartObj)
            SubItemObjList                  =table()
            if PartObj.IsValid
                NumPartSubItem              =PartObj.NumItems
                for PartSubItemIndex=1:NumPartSubItem
                    SubItemObj              =PartObj.GetItem(int32(PartSubItemIndex))
                    if SubItemObj.IsValid
                          SubItemName       =SubItemObj.GetName
                       if ~contains(SubItemName,'Plane') 
                           %&&  contains(SubItemName,'Circular')
                            SubItemObjList{end + 1} = SubItemObj;
                            
                       end
                    end
                end

            end

end