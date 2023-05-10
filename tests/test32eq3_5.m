a = 0.5; % modulation depth
w_e = 100; % modulation frequency in rad/s
t = linspace(0, pi/2/w_e, 1000); % time vector

% Compute y(t) based on the given equation
y = zeros(size(t));
for i = 1:length(t)
    if (w_e*t(i) >= 0) && (w_e*t(i) <= pi/6)
        y(i) = sqrt(3)*a*sin(w_e*t(i));
    elseif (w_e*t(i) > pi/6) && (w_e*t(i) <= pi/2)
        y(i) = a*sin(w_e*t(i) + pi/6);
    end
end

% Plot the waveform
plot(w_e*t, y);
xlabel('Time (s)');
ylabel('y(t)');
title('Saddle-shaped Modulation Waveform');
