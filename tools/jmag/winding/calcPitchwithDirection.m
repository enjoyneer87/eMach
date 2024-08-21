function [direction, pitch] = calcPitchwithDirection(GoSlot, ReturnSlot, NumSlots)
    % 기본적인 delta 계산
    delta = ReturnSlot - GoSlot;    
    %% 일단 forwardPitch라고 가정해놓고 reversePitch도 구하기
    forwardPitch = mod(delta, NumSlots);                   % forward 방향으로 회전할 때의 pitch 계산
    reversePitch = mod(NumSlots - forwardPitch, NumSlots); % reverse 방향으로 회전할 때의 pitch 계산   
    %% 방향 및 pitch 결정
    if forwardPitch <= reversePitch
        direction = 'forward';
        pitch = forwardPitch;
    else
        direction = 'reverse';
        pitch = reversePitch;
    end
    %% reverse 방향인 경우 pitch를 음수로 변환
    if strcmp(direction, 'reverse')
        pitch = -pitch;
    end
end