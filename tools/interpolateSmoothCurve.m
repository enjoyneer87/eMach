function [smoothed_power, interpolated_power] = interpolateSmoothCurve(speed, power, new_speed)
    % 등간격이 아닌 speed에 대한 power 데이터를 smoothing하고
    % 등간격의 속도에 대한 데이터로 변환하는 함수
    
    % 중복된 값을 unique 처리
    [unique_speed, idx] = unique(speed);
    unique_power = power(idx);
    
    % 시작점과 끝점을 원래 데이터와 동일하게 유지
    if unique_speed(1) > min(new_speed)
        unique_speed = [min(new_speed); unique_speed];
        unique_power = [interp1(unique_speed(2:end), unique_power, min(new_speed), 'linear'); unique_power];
    end
    
    if unique_speed(end) < max(new_speed)
        unique_speed = [unique_speed; max(new_speed)];
        unique_power = [unique_power; interp1(unique_speed(1:end-1), unique_power, max(new_speed), 'linear')];
    end
    
    % 속도에 대한 파워 데이터를 smoothing
    smoothed_power = smoothdata(unique_power, 'loess');
    
    % 속도와 파워 데이터를 등간격의 속도에 대해 보간
    interpolated_power = interp1(unique_speed, smoothed_power, new_speed, 'pchip');
end
