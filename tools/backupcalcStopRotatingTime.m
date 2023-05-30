% function rotating_time = backupcalcStopRotatingTime(rotor_mass, rotor_radius_mm, shaft_length_mm, shaft_radius_mm, target_speed)
    % mm 단위를 m 단위로 변환
    rotor_mass = rotor_mass ;  % kg
    rotor_radius = rotor_radius_mm / 1000;  % m
    shaft_length = shaft_length_mm / 1000;  % m
    shaft_radius = shaft_radius_mm / 1000;  % m
    
    % 관성모멘트 계산
    rotor_inertia = 0.5 * rotor_mass * ((shaft_radius))^2; % kg*m^2

    % 회전 속도 설정
    target_angular_velocity = 2 * pi * target_speed / 60;  % 목표 각속도 (rad/s)
    
    angular_deceleration=-target_angular_velocity^2/(2*rotor_inertia);

    rotating_time = target_angular_velocity / angular_deceleration * rotor_inertia;  % s
end
