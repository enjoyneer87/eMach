% eq 3.33 First Sideband
cos_phi_s_12 = ((sigma1*C12 - sigma2*C14)*sin(delta)) / sqrt(sigma1^2*C12^2 + sigma2^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta));
sin_phi_s_12 = -((sigma1*C12 + sigma2*C14)*cos(delta)) / sqrt(sigma1^2*C12^2 + sigma2^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta));


cos_phi_s_14 = ((sigma2*C12 - sigma1*C14)*sin(delta)) / sqrt(sigma2^2*C12^2 + sigma1^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta));
sin_phi_s_14 = ((sigma2*C12 + sigma1*C14)*cos(delta)) / sqrt(sigma2^2*C12^2 + sigma1^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta));


% 3.39 
cos_phi_s_21 = Ld*cos(delta)/sqrt(Ld^2*cos(delta)^2+Lq^2*sin(delta)^2);
sin_phi_s_21 = Lq*sin(delta)/sqrt(Ld^2*cos(delta)^2+Lq^2*sin(delta)^2);

% 3.41 Second Sideband
cos_phi_s_25 = (sigma1*C25 + sigma2*C27*cos(delta)) / sqrt(sigma1^2*C25^2 + sigma2^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta));
sin_phi_s_25 = (sigma1*C25 - sigma2*C27*sin(delta)) / sqrt(sigma1^2*C25^2 + sigma2^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta));
cos_phi_s_27 = (sigma2*C25 + sigma1*C27*cos(delta)) / sqrt(sigma2^2*C25^2 + sigma1^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta));
sin_phi_s_27 = -(sigma2*C25 - sigma1*C27*sin(delta)) / sqrt(sigma2^2*C25^2 + sigma1^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta));

