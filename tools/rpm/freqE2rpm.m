function rpm = freqE2rpm(freqE,polePair)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here

omegaE=freq2omega(freqE);  % [radsec] 각속도
omega = elec2mech(omegaE,polePair);
rpm = radsec2rpm(omega); % 

end