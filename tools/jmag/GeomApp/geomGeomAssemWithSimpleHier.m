function PartGeomTable=geomGeomAssemWithSimpleHier(geomApp)
%% getGeomPartRegionTable(geomApp)  - PartList
PartGeomTable = getGeomAssemItemListTable(geomApp,'Part');
geomDocu      = geomApp.GetDocument;
% Part 
    % Item
      % Sketch
        % sketch Feature
            % TregionItem
      % Extrude Solid
      % FaceExtrude Solid
%% geom
for PartIndex=1:height(PartGeomTable)
        PartObj        = PartGeomTable.AssemItem(PartIndex);
        % getGeomObjItemListTable - Part의 subItem들
        PartItemTable  = getGeomObjItemListTable(PartObj);
        ItemStruct = struct();        
        %% ItemObj
        for ItemIndex =1:height(PartItemTable)
            ItemObj        = PartItemTable.AssemItem{ItemIndex};
            ItemObjType    = PartItemTable.Type{ItemIndex};       
        %% Sketch
            if strcmp(ItemObjType,'Sketch')
                tempHierData   = table();
                sketchStruct.ItemObj     = ItemObj;
                sketchStruct.ItemObjType = ItemObjType;
                ItemObj.OpenSketch();
                % getGeomObjItemListTable - sketch의 subItem들
                sketchObjItemTable     = getGeomObjItemListTable(ItemObj);  
                cursketch_SubItemType  =unique(sketchObjItemTable.Type);
                Bool_Shape             =contains(cursketch_SubItemType,'sketch','IgnoreCase',true);
                Bool_contraint         =contains(cursketch_SubItemType,'constraint','IgnoreCase',true);
                %% Non Basic Shape Item
                cursketch_nonShape     =cursketch_SubItemType(~Bool_contraint&~Bool_Shape);
                if any(contains(cursketch_nonShape,'RegionCircularPattern'))
                AssemSubItemTable                       = sketchObjItemTable(strcmp(sketchObjItemTable.Type,'RegionCircularPattern'),:);
                % addRefObj2AssemTable
                AssemItemWithRefObjTable                = addRefObj2AssemTable(AssemSubItemTable,geomApp)  ;
                tempHierData                            = AssemItemWithRefObjTable;
                end

                if any(contains(cursketch_nonShape,'RegionItem')) 
                %% getRegionItemTable      - regionItem찾기
                AssemSubItemTable                       = sketchObjItemTable(strcmp(sketchObjItemTable.Type,'RegionItem'),:);
                % addRefObj2AssemTable
                AssemItemWithRefObjTable                = addRefObj2AssemTable(AssemSubItemTable,geomApp)  ;
                tempHierData                            = [tempHierData; AssemItemWithRefObjTable];
                end
                sketchStruct.RegionItem                 = tempHierData;
                % sketchStruct 2 ItemStruct
                ItemStruct(ItemIndex).sketchStruct = sketchStruct ;
        %% Extrude Solid Obj > geometry Obj(RefObj)
            elseif strcmp(ItemObjType,'ExtrudeSolid')
                % ItemObj();    
                % tempHierData={'test'};
                extrObj                                  =  geomDocu.CreateReferenceFromItem(ItemObj);
                tempHierData                             =  extrObj.GetIdentifier;
                ItemStruct(ItemIndex).ExtrudeSolid       =  tempHierData;
        %% FaceExtrudeSolid > geometry Obj(RefObj)
            elseif strcmp(ItemObjType,'FaceExtrudeSolid')
                %[TB]
                tempHierData={'test'};
                ItemStruct(ItemIndex).FaceExtrudeSolid=tempHierData;
                % end
            end
        end
        % PartGeomTable.RefObjListTable(PartIndex) = {RefObjListTable};
        PartGeomTable.ItemTableList(PartIndex)   ={ItemStruct};
        
end
%% end For
PartObj.ClosePart();
end
