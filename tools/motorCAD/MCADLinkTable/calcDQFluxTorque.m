function TorqueDq=calcDQFluxTorque(Idpks,Iqpk,Lamda_ds,Lamda_qs,PoleNumber)
   TorqueDq = 3/2*(-PoleNumber/2) * (Idpks .* Lamda_qs - Iqpk .* Lamda_ds);
end
