function StatorOneSlotAngle=findStatorOneSlotAngle(StatorGeomArcTable)

    % Angle 변수의 각도가 90도 이하인 행 찾기
    rows = StatorGeomArcTable.EndVertexTabletheta <= 90;
    
    % 조건을 만족하는 첫 번째 행의 값을 반환
    % StatorOneSlotAngle = StatorGeomArcTable.Angle(find(rows, 1));
    StatorOneSlotAngle = max(StatorGeomArcTable.EndVertexTabletheta(find(rows)));

end