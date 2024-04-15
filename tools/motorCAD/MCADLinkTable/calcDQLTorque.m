function TorqueDq=calcDQLTorque(idm_rms, iqm_rms, p, psi_pm, Ld, Lq)
    % Tdq 토크 계산 
    Idpk = idm_rms * sqrt(2);
    Iqpk = iqm_rms * sqrt(2);
    TorqueDq = (3/2) *p/2*(psi_pm.* Iqpk + (Ld - Lq) .* Idpk .* Iqpk);
end