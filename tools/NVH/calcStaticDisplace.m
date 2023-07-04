function x_ms = calcStaticDisplace(F_hat, K_m)
    [m_len, n_len] = size(F_hat);
    x_ms = zeros(m_len, n_len);
    % Force Density - [N/m^2]
    % S Surface  [m^2]
%     p(m,n)=F_hat;
%     F_hat(m, n)=p(m,n)*S;
    % Displacement -  [mm]
    % Lumped Stiffness - [Mn/m]
    for m = 1:m_len
        for n = 1:n_len
            x_ms(m, n) = F_hat(m, n) / K_m(m);
            % m *10*e3= [N/m^2]/[Mn/m] = 1/(M
        end
    end
end
