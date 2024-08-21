function [NewWindingTable, SlotArray] = renumberMCADSlotNumber(McadWindingPatternTable, reverseOrder)

    %% SlotTable
    SlotTable = McadWindingPatternTable(contains(McadWindingPatternTable.TypeofData, 'Slot'), "ValueTable");
    NewWindingTable = McadWindingPatternTable;

    %% Slot +1
    SlotCell = table2array(SlotTable);
    SlotArray = str2double(SlotCell);

    if any(SlotArray == 0)
        numericArray = SlotArray + 1;
    else
        numericArray = SlotArray;
    end
    
    if nargin>1
        %% Reverse Slot Number Order if requested
        if reverseOrder
            maxSlot = max(numericArray);
            numericArray = maxSlot - numericArray + 1;
        end
    end
    cellArray = cellfun(@num2str, num2cell(numericArray), 'UniformOutput', false);
    NewWindingTable(contains(McadWindingPatternTable.TypeofData, 'Slot'), "ValueTable") = cellArray;
    
    % Return only NewWindingTable if SlotArray is not requested
    if nargout < 2
        clear SlotArray
    end
end