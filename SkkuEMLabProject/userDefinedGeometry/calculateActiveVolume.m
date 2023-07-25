function res = calculateActiveVolume(Stator_OD, Active_Length)
    res = pi * (Stator_OD^2) / 4 * Active_Length * 1e-9;
end
