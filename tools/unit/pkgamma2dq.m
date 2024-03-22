function [id, iq] = pkgamma2dq(amplitude, phaseAdvance)
    phaseAdvanceRad = (phaseAdvance + 90) * pi / 180;  % Convert phase advance to radians
    id = amplitude .* cos(phaseAdvanceRad);  % d-axis current component
    iq = amplitude .* sin(phaseAdvanceRad);  % q-axis current component
end
