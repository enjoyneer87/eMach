function force_newtons = watt2Force(power_watts, speed_kph)
    % Convert kph to m/s
    speed_ms = kph2ms(speed_kph);

    % Calculate force in newtons
    force_newtons = power_watts ./ speed_ms;
end
