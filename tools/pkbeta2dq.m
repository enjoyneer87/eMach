function [id, iq] = pkbeta2dq(amplitude, phaseAdvance)
        %% beta is not phase Advance actually in MotorCAD, gamma is phaseAdvance, gamma+90=beta
    phaseAdvanceRad = (phaseAdvance + 90) * pi / 180;  % Convert phase advance to radians
    id = amplitude .* cos(phaseAdvanceRad);  % d-axis current component
    iq = amplitude .* sin(phaseAdvanceRad);  % q-axis current component
end
