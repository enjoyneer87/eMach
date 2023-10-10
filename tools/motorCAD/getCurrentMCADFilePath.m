function b=getCurrentMCADFilePath(mcad)
    % mcad(1).ShowMagneticContext()
    [~,b]=mcad.GetVariable('CurrentMotFilePath_MotorLAB');
    disp(b)
end
