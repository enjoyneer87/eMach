function [fftXSideAmp,fftYSideAmp, diffnormal] = FFTdiff(x,y)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here
Nx=length(x);
fftX= fft(x);
fftXSide = fftX(1:Nx/2);
fftXSideAmp = abs(fftXSide)/(Nx/2);
Ny=length(y);
fftY= fft(y);
fftYSide = fftY(1:Ny/2);
fftYSideAmp = abs(fftYSide)/(Ny/2);

diff=fftXSide-fftYSide;
diffnormal=abs(diff)/(Ny/2);

end