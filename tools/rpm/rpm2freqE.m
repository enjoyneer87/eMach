function freqE = rpm2freqE(rpm,polePair)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here

omega=rpm2radsec(rpm);
omegaE = mech2elec(omega,polePair);
freqE=omega2freq(omegaE);
% radsec=
% rpm/60*2*pi()*polePair/(2*pi);
end