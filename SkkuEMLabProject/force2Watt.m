function power_watts = force2Watt(force_newtons, speed_kph)
    % Convert kph to m/s
    speed_ms = kph2ms(speed_kph);

    % Calculate power in watts
    power_watts = force_newtons .* speed_ms;
end
