function runnerType=checkInnerOuterMotor(StatorGeomArcTable,RotorGeomArcTable)

StatorMaxRadius=max(StatorGeomArcTable.Radius);
StatorMinRadius=min(StatorGeomArcTable.Radius);
RotorMaxRadius=max(RotorGeomArcTable.Radius);
RotorMinRadius=min(RotorGeomArcTable.Radius);

if StatorMaxRadius<RotorMinRadius
    runnerType='OuterRotor';
elseif RotorMaxRadius<StatorMinRadius
     runnerType='InnerRotor';
end


end