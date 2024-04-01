function TorqueDq=calcDQLTorque(idm, iqm, p, psi_pm, Ld, Lq)
    % Tdq 토크 계산
    TorqueDq = (3/2) *p/2*(psi_pm.* iqm + (Ld - Lq) .* idm .* iqm);
end