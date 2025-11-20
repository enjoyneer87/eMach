function StatorOneSlotAngle=findStatorOneSlotAngle(StatorGeomArcTable)
    %% JMAG GeomTable
    if istable(StatorGeomArcTable) && isvar(StatorGeomArcTable,'EndVertexTabletheta')
        % Angle 변수의 각도가 90도 이하인 행 찾기
        rows = StatorGeomArcTable.EndVertexTabletheta <= 90;
        
        % 조건을 만족하는 첫 번째 행의 값을 반환
        % StatorOneSlotAngle = StatorGeomArcTable.Angle(find(rows, 1));
        StatorOneSlotAngle = max(StatorGeomArcTable.EndVertexTabletheta(find(rows)));
        %% [TB] 주기성 check후 동작 필요  DXF Entities (Matlab)
        % elseif istable(StatorGeomArcTable) && isvar(StatorGeomArcTable,'arc')
        % max_angle = getMaxObjectAngle(entitiesTable);
        % StatorOneSlotAngle = 360/max_angle;
    elseif isnumeric(StatorGeomArcTable)
      StatorOneSlotAngle = 360/StatorGeomArcTable;
    end
end