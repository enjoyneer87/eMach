% eq 3.32

Is_12 = (Udc*sqrt((sigma1^2*C12^2 + sigma2^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta))) / (4*(w_s + 2*w_e)));
Is_14 = (Udc*sqrt((sigma2^2*C12^2 + sigma1^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta))) / (4*(w_s + 4*w_e)));

% 3.38

Is_21 = - (Udc*C21)/(4*w_s)*sqrt((sin(delta)/Ld)^2 + (cos(delta)/Lq)^2);
% 3.40
Is_25 = Udc * sqrt(sigma1^2*C25^2 + sigma2^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta)) / (4*(2*w_s + 6*w_e));
Is_27 = Udc * sqrt(sigma2^2*C25^2 + sigma1^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta)) / (4*(2*w_s + 6*w_e));
