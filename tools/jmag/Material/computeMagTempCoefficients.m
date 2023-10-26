function [alpha, beta] = computeMagTempCoefficients(Br1, Hcj1, Br2, Hcj2, T1, T2)
    % Compute temperature coefficients alpha and beta
    
    if T1 == T2
        error('The two temperatures should not be the same.');
    end
    
    alpha = 100 * (Br2 - Br1) / (Br1 * (T2 - T1));
    beta = 100 * (Hcj2 - Hcj1)/ (Hcj1* (T2 - T1));

end
