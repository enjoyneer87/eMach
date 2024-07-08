function removeRegionExceptPartName(NameStruct,RegionTablePerType,geomApp)
% NameStruct=StatorNameStruct
% RegionTablePerType=StatorRegionTablePerType
RegionNameCell          =NameStruct.RegionNameCell;
AssembleItemName        =NameStruct.PartNameList;
uniqueRegionNameCell    =NameStruct.uniqueRegionNameCell;
SketchItem              =NameStruct.SketchName;

%% geomApp
geomDocu=geomApp.GetDocument;
geomAssem=geomDocu.GetAssembly;
%%
    for CopiedPartIndex=1:length(uniqueRegionNameCell)
    Name2Change             =uniqueRegionNameCell{CopiedPartIndex};
    object2Change           =AssembleItemName{CopiedPartIndex};
    
    % 지우지않을 리스트와 지울리스트 분류
    if ~isempty(Name2Change)
    RegionListConserve   = detGeomRegionsName(RegionTablePerType,Name2Change);
    [RegionList2Delete, ~, ~] = findUniqueAndNonUniqueStrings(RegionNameCell, RegionListConserve);     
    RegionRefObjList2Delete=findRefObjFromRegionTablePerType(RegionTablePerType,RegionList2Delete);
    end
    % Init
    geomAssem.GetItem(object2Change).SetProperty("Name", Name2Change)
    changedObjectPartItem=geomAssem.GetItem(Name2Change);
    changedObjectPartItem.OpenPart()
    SketchObj=changedObjectPartItem.GetItem(SketchItem);
    SketchObj.OpenSketch();
        % if any(contains(RegionListConserve,'Rotor','IgnoreCase',true))
        % BooleanObj=SketchObj.GetItem('Boolean');
        % if ~(BooleanObj.IsValid)
        % BooleanObj=SketchObj.CreateBoolean();
        % end
        % for ConserveListIndex=1:length(RegionListConserve)
        %     BooleanObj.SetProperty("Region1", RegionListConserve{ConserveListIndex});
        % end
        % for DeleteListIndex=1:length(RegionList2Delete)
        %     sel=geomApp.GetDocument().GetSelection();
        %     sel.AddReferenceObject(RegionRefObjList2Delete{DeleteListIndex})
        %     sel.CountReferenceObject
        %     BooleanObj.SetProperty("Region2", RegionList2Delete{DeleteListIndex});
        % end
        % BooleanObj.SetProperty('DeleteRegion2',1)
        % else
        geomApp.GetDocument().GetSelection().Clear();
        
        % 지울리스트 객체 선택
        for RegionNameCellIndex=1:length(RegionList2Delete)
            Region2Delete=RegionList2Delete{RegionNameCellIndex};
            if ~strcmp(Region2Delete,Name2Change)
            geomApp.GetDocument().GetSelection().Add(changedObjectPartItem.GetItem(SketchItem).GetItem(Region2Delete))
            end
        end
        % 지우기
        % geomDocu=geomApp.GetDocument()
        % geomSel=geomDocu.GetSelection
        % 
        geomApp.GetDocument().GetSelection().Delete()
        %
        geomApp.GetDocument().GetSelection().Add(changedObjectPartItem.GetItem(SketchItem).GetItem("Boolean"))
        geomApp.GetDocument().GetSelection().Delete()        
        changedObjectPartItem.GetItem(SketchItem).CloseSketch()
        changedObjectPartItem.ClosePart()
    end
end



