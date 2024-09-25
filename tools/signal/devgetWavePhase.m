function devgetWavePhase(x)

Fs = 100;
t = 0:1/Fs:1-1/Fs;
x = cos(2*pi*15*t - pi/4) 

% + cos(2*pi*40*t + pi/2);

y = fft(x);
z = fftshift(y);

ly = length(y);
f = (-ly/2:ly/2-1)/ly*Fs;
stem(f,abs(z))
title("Double-Sided Amplitude Spectrum of x(t)")
xlabel("Frequency (Hz)")
ylabel("|y|")
grid

tol = 1e-6;
z(abs(z) < tol) = 0;

theta = angle(z);

stem(f,theta/pi)
title("Phase Spectrum of x(t)")
xlabel("Frequency (Hz)")
ylabel("Phase/\pi")
grid
end