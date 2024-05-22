function runnerType=checkInnerOuterMotor(StatorGeomArcTable,RotorGeomArcTable)

StatorMaxRadius=max(StatorGeomArcTable.StartVertexTabler);
StatorMinRadius=min(StatorGeomArcTable.StartVertexTabler);
RotorMaxRadius=max(RotorGeomArcTable.StartVertexTabler);
RotorMinRadius=min(RotorGeomArcTable.StartVertexTabler);

if StatorMaxRadius<RotorMinRadius
    runnerType='OuterRotor';
elseif RotorMaxRadius<StatorMinRadius
     runnerType='InnerRotor';
end


end