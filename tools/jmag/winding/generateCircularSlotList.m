function SlotList2 = generateCircularSlotList(startSlot, stepSize, totalSlots)
    % generateCircularSlotList - 슬롯 번호를 순환하여 생성하는 함수
    %
    % Syntax: SlotList2 = generateCircularSlotList(startSlot, stepSize, totalSlots)
    %
    % Inputs:
    %   startSlot  - 시작 슬롯 번호 (예: 17)
    %   stepSize   - 슬롯 번호 간격 (예: 6)
    %   totalSlots - 슬롯의 총 수 (예: 48)
    %
    % Outputs:
    %   SlotList2 - 순환된 슬롯 번호 리스트
    
    SlotList2 = [];
    currentSlot = startSlot;

    while length(SlotList2) < totalSlots / stepSize
        SlotList2(end + 1) = currentSlot;
        currentSlot = mod(currentSlot - 1 + stepSize, totalSlots) + 1;
    end
end