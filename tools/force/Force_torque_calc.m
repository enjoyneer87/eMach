function [Fr,Ft,Torque_av]=Force_torque_calc(fr,ft,radius,Lstk)


% In pyleecan  ,
% period(ic) [deg]
% periodic=45;
% periodic_force=360/periodic;        % Force가 기계적으로 몇번 반복인지
periodic_force=1;
circum_div =length(fr);
rtheta=radius*2*pi()/periodic_force/circum_div;                    % Rtheta 계산

Fr= fr*rtheta*Lstk;   
Ft= ft*rtheta*Lstk;

% ft*radius;
Torque_av=sum(Ft'*radius);
plot([0:360/size(Torque_av,2):360-360/size(Torque_av,2)],Torque_av)
xlabel('Mech Angle [deg]')
xlim([0 360])
xticks([0:30:360])
xticklabels(0:30:360)
title('Electromagnetic Torque [N] in Maxwell Stress Tensor')
grid on
box on
end