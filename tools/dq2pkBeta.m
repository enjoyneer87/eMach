function [amplitude phaseAdvance]=dq2pkBeta(id,iq)
% dq 전류 값
% id = inpowerskew.Id; % d 축 전류
% iq = inpowerskew.Iq; % q 축 전류

amplitude = sqrt(id.^2 + iq.^2);  % 크기
phaseAdvance = rad2deg(atan2(iq, id));

% * 180/pi-90;  % 방향

end