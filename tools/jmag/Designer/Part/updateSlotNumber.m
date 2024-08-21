%% Slot 번호 업데이트 함수
function updatedName = updateSlotNumber(name, slotNumber)
    slotStart = strfind(name, 'Slot');
    if isempty(slotStart)
        updatedName = name;
        return;
    end
    slashPos = strfind(name(slotStart:end), '/') + slotStart - 1;
    if isempty(slashPos)
        updatedName = [name(1:slotStart+3), num2str(slotNumber)];
    else
        updatedName = [name(1:slotStart+3), num2str(slotNumber), name(slashPos:end)];
    end
end
