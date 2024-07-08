function geomItem=getGeomItem(ItemObj, ItemObjIndex)
    % saveItemData - Recursively saves the data of ItemObj and its subitems
    %
    % Syntax: saveItemData(ItemObj, ItemObjIndex)
    %
    % Inputs:
    %    ItemObj - The main object containing items
    %    ItemObjIndex - The index of the current item in ItemObj
    %
    % Example:
    %    saveItemData(mainItemObj, 1)

    % Initialize storage structure if not already present
    persistent savedData;
    if isempty(savedData)
        savedData = struct('AssemItemObj', {},'Name', {}, 'Type', {}, 'NumItems', {}, 'subItem', {});
    end

    % Save main item data
    savedData(ItemObjIndex).AssemItemObj=ItemObj;
    savedData(ItemObjIndex).Name = ItemObj.GetName;
    savedData(ItemObjIndex).Type = ItemObj.GetScriptTypeName;
    ItemObj.OpenPart;
    savedData(ItemObjIndex).NumItems = ItemObj.NumItems;
    
    NumItems = ItemObj.NumItems;
    if NumItems ~= 0
        savedData(ItemObjIndex).subItem = struct('AssemItemObj', {},'Name', {}, 'Type', {}, 'NumItems', {}, 'subItem', {});
        for subItemIndex = 1:NumItems
            subItemObj = ItemObj.GetItem(int32(subItemIndex-1));
            savedData(ItemObjIndex).subItem(subItemIndex) = getGeomSubItem(subItemObj);
        end
    end
    
    % Display saved data for verification
    geomItem=savedData;
end
