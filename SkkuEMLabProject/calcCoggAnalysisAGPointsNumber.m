function NPointsofAGMotorCAD=calcCoggAnalysisAGPointsNumber(Pole,Slots,PointPer1ElecCycle)
    Npoles      = Pole; 
    Nslot       = Slots;
    numberGcd=gcd(Npoles,Nslot)
    ModelPeriodicNumber = Pole
    pointPerElecCycle=PointPer1ElecCycle

    coggPeriodMechAngle=360*numberGcd/(Nslot*Npoles)
    rotationStepMechaAngle=coggPeriodMechAngle/pointPerElecCycle
    N=1;
    AirGapMeshPointsinCircum=N*Npoles*Nslot*pointPerElecCycle/numberGcd
    PeriodModelAirGapPoints=AirGapMeshPointsinCircum
    NPointsofAG =AirGapMeshPointsinCircum;
    NPointsofAGMotorCAD =NPointsofAG;
    
    NPointsofAGJMAG =NPointsofAG/ModelPeriodicNumber;   

end

