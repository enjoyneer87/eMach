function b=getMCADLabFilePath(mcad)
    % mcad(1).ShowMagneticContext()
    [~,b]=mcad.GetVariable('ResultsPath_MotorLAB');
    disp(b)
end
