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
        ItemTableStruct = struct();        
        %% ItemObj
        for ItemIndex =1:height(PartItemTable)
        ItemObj        = PartItemTable.AssemItem{ItemIndex};
        ItemObjType    = PartItemTable.Type{ItemIndex};         
        %% Sketch
            if strcmp(ItemObjType,'Sketch')
            ItemObj.OpenSketch();
            % getGeomObjItemListTable - sketch의 subItem들
            sketchObjItemTable                  = getGeomObjItemListTable(ItemObj);    
            % getRegionItemTable      - regionItem찾기
            AssemRegionTable                    = sketchObjItemTable(strcmp(sketchObjItemTable.Type,'RegionItem'),:);
            % addRefObj2AssemTable
            AssemItemWithRefObjTable            = addRefObj2AssemTable(AssemRegionTable,geomApp)  ;
            tempHierData                        = AssemItemWithRefObjTable;
            ItemTableStruct(ItemIndex).Sketch   = tempHierData;
        %% Extrude Solid Obj > geometry Obj(RefObj)
            elseif strcmp(ItemObjType,'ExtrudeSolid')
            % ItemObj();    
            % tempHierData={'test'};
            extrObj                                  =  geomDocu.CreateReferenceFromItem(ItemObj);
            tempHierData                             =  extrObj.GetIdentifier;
            ItemTableStruct(ItemIndex).ExtrudeSolid  =  tempHierData;
        %% FaceExtrudeSolid > geometry Obj(RefObj)
            elseif strcmp(ItemObjType,'FaceExtrudeSolid')
            %[TB]
            tempHierData={'test'};
            ItemTableStruct(ItemIndex).FaceExtrudeSolid=tempHierData;
            % end
            end
        end
        % PartGeomTable.RefObjListTable(PartIndex) = {RefObjListTable};
        PartGeomTable.ItemTableList(PartIndex)   ={ItemTableStruct};
        
end
%% end For
PartObj.ClosePart();
end
