function AssemObjStruct=getSkecthDataTableFromCurrentSelection(geomApp)
   % geomApp=app.CreateGeometryEditor(0);
   % geomDocu=geomApp.GetDocument();


   
   
   %%
    % sel=geomDocu.GetSelection;
   sel      =mkSelectionObj(geomApp,1);
    % 
    % NumSelections=sel.Count;    
    NumSelections=sel.CountReferenceObject;
   


    %% 
    AssemObjStruct=struct();
    for SelIndex=1:NumSelections
        % Item=sel.Item(SelIndex-1);
        % if Item.IsValid==1                
            % AssemObjStruct(SelIndex).ReferenceObj        =geomDocu.CreateReferenceFromItem(Item);
            AssemObjStruct(SelIndex).ReferenceObj        =sel.GetReferenceObject(SelIndex-1);
          
            AssemObjStruct(SelIndex).IdentifierName      =AssemObjStruct(SelIndex).ReferenceObj.GetIdentifier;
            AssemObjStruct(SelIndex).Id                  =AssemObjStruct(SelIndex).ReferenceObj.GetId;
            % 
            % AssemObjStruct(SelIndex).Name              =Item.GetName;
            % AssemObjStruct(SelIndex).Type              =Item.GetScriptTypeName;
            % sel.AddReferenceObject(RegionData(SelIndex).ReferenceObj)
        % end
    end

     for SelIndex=1:NumSelections
            CurItem=convertRefObj2Item(AssemObjStruct(SelIndex).ReferenceObj,geomApp);
         if CurItem.IsValid==1                
            AssemObjStruct(SelIndex).Name              =CurItem.GetName;
            AssemObjStruct(SelIndex).Type              =CurItem.GetScriptTypeName;
         end
     end

    sel.Clear;
end
