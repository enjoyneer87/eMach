function [fr,ft]=force_density_calc(B_rad,B_tan)
u0=4*pi*(10^-7);
fr_be = (B_rad.*B_rad - B_tan.*B_tan)/(2*u0); %*rtheta*Lstk;              % Radial Force 계산
ft_be = (B_rad.*B_tan)/u0; %*rtheta*Lstk;                           % Tangential Force 계산
fr=fr_be;
ft=ft_be;

return 