function [rpm,omega] = freq2rpm(freq)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here

omega=freq2omega(freq);  % [radsec] 각속도
rpm = radsec2rpm(omega); % 

end