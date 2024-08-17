function [modifiedTable, additionalTable] = modify_coil_table(CoilTableCell, PhaseIndex, ppIndex, NumCoil)
    % CoilTableCell에서 (PhaseIndex, ppIndex) 위치의 테이블을 가져옵니다.
    originalTable = CoilTableCell{PhaseIndex, ppIndex};
    
    % NumCoil 이하의 값만 남기고, 나머지는 별도의 테이블로 이동합니다.
    % 여기서는 originalTable이 단순 숫자 배열이라고 가정합니다.
    % originalTable이 다른 형식일 경우 이 코드를 수정해야 할 수 있습니다.
    modifiedTable = originalTable(originalTable <= NumCoil);
    additionalTable = originalTable(originalTable > NumCoil);

    % additionalTable에서 1부터 다시 넘버링합니다.
    if ~isempty(additionalTable)
        additionalTable = additionalTable - min(additionalTable) + 1;
    end
end

% 예시 사용법:
% [modifiedTable, additionalTable] = modify_coil_table(CoilTableCell, 1, 1, 10);
