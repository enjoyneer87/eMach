function PeriodModelAirGapPoints=calcAGPoint(pole,pointPerElecCycle)

% 1)calc Simulation Period 
periodMechAngle=360/pole;

% 2)calc Rotation Step
RotationAngleinMechAngle = periodMechAngle/pointPerElecCycle;

%3) calc Number of Airgap Point
N=1;
AirGapMeshPointsinCircum=N*360/RotationAngleinMechAngle;
PeriodModelAirGapPoints=AirGapMeshPointsinCircum;

end