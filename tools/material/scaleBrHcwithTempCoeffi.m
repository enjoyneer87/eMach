function [Br_temp, Hcj_temp] = scaleBrHcwithTempCoeffi(Br_Tref, Hcj_Tref, Magnet_temp, Tref, alpha, beta)
    % Temperature adjusted Br and Hcj values
    Br_temp = Br_Tref * (1 + (alpha * (Magnet_temp - Tref) / 100));
    Hcj_temp = Hcj_Tref * (1 + (beta * (Magnet_temp - Tref) / 100));
end
