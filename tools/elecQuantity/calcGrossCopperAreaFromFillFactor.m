function MotorCADGeo=calcGrossCopperAreaFromFillFactor(MotorCADGeo,fillfactor)
    if nargin<2
    fillfactor=MotorCADGeo.GrossSlotFillFactor;
    end

    if fillfactor>1
        fillfactor=fillfactor/100; % fillfactor in [%] 
    end

    
    copperArea=fillfactor*(MotorCADGeo.Area_Slot); %% [mm] unit
    % copperArea=fillfactor*(); %% [mm] unit
    fillfactorWithNoWedge=copperArea/MotorCADGeo.Area_Slot_NoWedge;

    MotorCADGeo.fillfactorWithNoWedge=fillfactorWithNoWedge;
    MotorCADGeo.copperArea=copperArea;
    % if varargin{3}==1
    % copperArea=copperArea*mm2m(1)*mm2m(1);
    % end
    
end