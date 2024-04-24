function    BuildingData=checkMCADLABMaxModelCurrent(BuildingData)

    if BuildingData.MotorCADGeo.CurrentSpec_MotorLAB==0
    Imaxpk=BuildingData.MotorCADGeo.MaxModelCurrent_MotorLAB;
    Imaxrms= Imaxpk/sqrt(2);
    Imax=Imaxpk;
    elseif double(BuildingData.MotorCADGeo.CurrentSpec_MotorLAB)==1   
    Imaxrms=BuildingData.MotorCADGeo.MaxModelCurrent_RMS_MotorLAB;
    Imaxpk = Imaxrms*sqrt(2);
    Imax=Imaxrms;
    end
    BuildingData.MotorCADGeo.Imaxpk                          = Imaxpk ;
    BuildingData.MotorCADGeo.Imaxrms                         = Imaxrms;

end