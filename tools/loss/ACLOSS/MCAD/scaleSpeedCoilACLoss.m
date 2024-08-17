function Pcoil_AC_scaled = scaleSpeedCoilACLoss(Pcoil_AC_build, omega_build, omega_op,zeta)
    % 입력 매개변수 설명:
    % Pcoil_AC_build: omega_build에서 계산한 코일 AC 손실
    % omega_op: 운영 각속도
    % omega_build: 빌드 각속도
    % zeta: 스케일링 지수
    
    if nargin<4
        zeta=2;
    end
    % 각속도에 따른 AC 손실 스케일링
    Pcoil_AC_scaled = (omega_op / omega_build)^zeta * Pcoil_AC_build;
end
