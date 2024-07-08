function TorqueDq = calcDQFluxTorque(Idrms, Iqrms, Lamda_ds, Lamda_qs, PoleNumber)
% function TorqueDq=calcDQFluxTorque(Id,Iq,Lamda_ds,Lamda_qs,p)  
% 전류 값을 RMS에서 피크로 변환
   Idpk = rms2pk(Idrms);
   Iqpk = rms2pk(Iqrms);

   % 토크 계산 (피크 전류값 사용)
   TorqueDq = (3/2) .* (-PoleNumber/2) .* (Idpk .* Lamda_qs - Iqpk .* Lamda_ds);
   % TorqueDq = -p/2 * (Id .* Lamda_qs - Iq .* Lamda_ds);

end
