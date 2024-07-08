
function subData = getGeomSubItem(subItemObj)
    % saveSubItemData - Recursively saves the data of subItemObj and its subitems
    %
    % Syntax: subData = saveSubItemData(subItemObj)
    %
    % Inputs:
    %    subItemObj - The sub-item object containing items
    %
    % Outputs:
    %    subData - The structure containing the saved sub-item data
    %
    % Example:
    %    subData = saveSubItemData(subItemObj)

    % Initialize sub-item data structure
    subData = struct('AssemItemObj', {},'Name', {}, 'Type', {}, 'NumItems', {}, 'subItem', {});

    % Save sub-item data
    subData(1).AssemItemObj = subItemObj;
    subData(1).Name      = subItemObj.GetName;
    subData(1).Type      = subItemObj.GetScriptTypeName;
    subData(1).NumItems  = subItemObj.NumItems;
    
    NumSubItems = subItemObj.NumItems;
    if NumSubItems ~= 0
        subData.subItem = struct('AssemItemObj', {},'Name', {}, 'Type', {}, 'NumItems', {}, 'subItem', {});
        for subSubItemIndex = 1:NumSubItems
            subSubItemObj = subItemObj.GetItem(subSubItemIndex-1);
            subData.subItem(subSubItemIndex) = getGeomSubItem(subSubItemObj);
        end
    end
end