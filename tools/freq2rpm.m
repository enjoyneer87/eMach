function [rpm,omega] = freq2rpm(freqE,p)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here

omegaE=freq2omega(freqE);

% rpm=2*pi*freq*60/((p/2)*2*pi)
rpm=omegaE*60/(p/2*2*pi);

% rpm=freq*60/(p/2);
end