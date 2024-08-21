%% Wire 또는 Conductor 번호 업데이트 함수
function updatedName = updateWireNumber(name, wireNumber)
    if contains(name, 'Wire', 'IgnoreCase', true)
        wireStart = strfind(name, 'Wire');
        updatedName = [name(1:wireStart+3), num2str(wireNumber)];
    else
        condStart = strfind(name, 'Conductor');
        updatedName = [name(1:condStart+8), num2str(wireNumber)];
    end
end