function MagStruct=convertLayerMagStructFromPartStructByType(PartStructByType)
% Unique Area
MagnetTable=PartStructByType.MagnetTable;
MagArea=uniquetol(MagnetTable.Area);
tempMagLayer=length(MagArea);
% CentroidPosition

    for LayerIndex=1:tempMagLayer
        tolerance = 0.1;  % 허용 오차 범위를 여기에 설정 (원하는 값으로 변경)
        % MagnetTable.Area와 MagArea(1)를 비교하면서 오차 범위 내에 있는지 확인
        logicalIndices = abs(MagnetTable.Area - MagArea(LayerIndex)) <= tolerance;
        
        % 오차 범위 내에 있는 행을 선택하여 필터링
        filteredT = MagnetTable(logicalIndices, :);
        MagStruct(LayerIndex).MagnetTable=filteredT;
        for MagnetIndex=1:height(filteredT)
        MagnetR(MagnetIndex)=filteredT.CentroidR(MagnetIndex);
        end
        MagStruct(LayerIndex).MinimumRadiusMagnet=min(MagnetR);
        MagStruct(LayerIndex).MagnetCenterRadius=MagnetR;
    end

[~,index1] = sortrows([MagStruct.MinimumRadiusMagnet].', "descend");
MagStruct = MagStruct(index1);
end

