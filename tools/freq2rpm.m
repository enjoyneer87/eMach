function [rpm,omega] = freq2rpm(freq,p)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here

omega=freq2omega(freq);

% rpm=2*pi*freq*60/((p/2)*2*pi)
rpm=omega*60/(p/2*2*pi);

% rpm=freq*60/(p/2);
end