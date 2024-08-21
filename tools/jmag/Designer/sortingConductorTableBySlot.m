function ConductorPartTable = sortingConductorTableBySlot(PartStruct,app)
    %%dev
    % PartStruct=PartStructByType.ConductorTable
    %% 초기 설정
    difftolerance = 1e-5;
    
    % PartStruct가 구조체일 경우 테이블로 변환
    if isstruct(PartStruct)
        PartTable = struct2table(PartStruct);
    elseif istable(PartStruct)
        PartTable = PartStruct;
    end
    
    %% ConductorPart 추출
    ConductorPartTable = PartTable(contains(PartTable.Name, 'Conductor'), :);
    if isempty(ConductorPartTable)
        ConductorPartTable = PartTable(contains(PartTable.Name, 'Wire', 'IgnoreCase', true), :);
    end
   
    %% 고유한 ConductorR과 SlotTheta 값 추출
    ConductorR = uniquetol(ConductorPartTable.CentroidR, difftolerance);
    ConductorR =sortrows(ConductorR,'descend');
    SlotTheta = uniquetol(ConductorPartTable.CentroidTheta, difftolerance);
    
    %% Slot 번호 할당
    for i = 1:length(SlotTheta)
        SlotIndex = abs(ConductorPartTable.CentroidTheta - SlotTheta(i)) < difftolerance;
        
        % Slot 번호가 이미 포함된 이름에서 번호를 업데이트
        SlotNames = ConductorPartTable.Name(SlotIndex);
        slotPos = contains(SlotNames, 'Slot', 'IgnoreCase', true);
        
        if any(slotPos)
            SlotNames(slotPos) = cellfun(@(name) updateSlotNumber(name, i), SlotNames(slotPos), 'UniformOutput', false);
        else
            SlotNames = strrep(SlotNames, '/', ['/Slot', num2str(i), '/']);
        end
        
        ConductorPartTable.Name(SlotIndex) = SlotNames;
    end
    
    %% Wire/Conductor 번호 할당
    for j = 1:length(ConductorR)
        WireIndex = abs(ConductorPartTable.CentroidR - ConductorR(j)) < difftolerance;
        WireNames = ConductorPartTable.Name(WireIndex);
        
        % Wire 또는 Conductor 번호를 업데이트
        WireNames = cellfun(@(name) updateWireNumber(name, j), WireNames, 'UniformOutput', false);
        
        ConductorPartTable.Name(WireIndex) = WireNames;
    end
    
    % 최종적으로 이름 기준으로 정렬
    ConductorPartTable = sortrows(ConductorPartTable, "Name", "ascend");

    % Chnage Name
    changeJMAGPartNameTable(ConductorPartTable,app);

  
    %% 최종적으로 PartStruct에 업데이트된 ConductorPartStruct 반영
    if isstruct(PartStruct)
        %% 테이블을 다시 구조체로 변환
        ConductorPartStruct = table2struct(ConductorPartTable);
    
        % 원래 구조체의 크기와 순서를 유지하면서 업데이트
        PartStruct(contains({PartStruct.Name}, {ConductorPartStruct.Name})) = ConductorPartStruct;
        ConductorPartTable=PartStruct;
    end

end
