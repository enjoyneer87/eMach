syms t; % t를 심볼릭 변수로 선언합니다.

% 주어진 식에 나오는 상수값들을 입력합니다.
A00 = 1; 
A01 = 2;
B01 = 3;
A10 = 4;
B10 = 5;
A11 = 6;
B11 = 7;
omega = 2*pi*10; % 각주파수
m = 1; % 조향신호의 차조주파수
omega_c = 2*pi*100; % 캐리어 주파수

vdc=540
Vm=360
Vm3=10


n = [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]
Aij=compute_Aij(vdc, Vm, Vm3, n)
% 주어진 식을 코드로 표현합니다.
va = (A00/2) + symsum(A0j*cos(j*omega*t) + B0j*sin(j*omega*t), j, 1, Inf) + ...
     symsum(Ai0*cos(m*omega_c*t) + Bi0*sin(m*omega_c*t), i, 1, Inf) + ...
     symsum(Aij*cos((i*omega_c+j*omega)*t) + Bij*sin((i*omega_c+j*omega)*t), ...
            i, 1, Inf, j, -Inf, Inf, @(i,j) j~=0);

% 결과를 출력합니다.
pretty(va);
