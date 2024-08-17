function Wmag_scaled = scaleSpeedMagnetLoss(Wmag_ref, MachineData, n,zeta)
    % 입력 매개변수 설명:
    % Wmag_ref: 참조 속도 n_ref 및 참조 온도 Tmag_ref에서의 영구자석 손실량
    % n: 현재 속도
    % n_ref: 참조 속도
    % Tmag: 현재 온도
    % Tmag_ref: 참조 온도
    % L: 모터의 길이
    % w: 모터의 폭
    % zeta: 속도에 대한 스케일링 지수 (기본값 2)
    
    if nargin<6
        zeta=2;
    end
    

    % 2D에서 3D로의 보정 계수 계산
    % fWmag_2Dto3D = (3/4) * (L^2) / (w^2 + L^2);
    n_ref=MachineData.LabBuildData.n2ac_MotorLAB;
    % 속도에 따른 스케일링 계수 계산
    speedScalingFactor = (n / n_ref)^zeta;
    
    % 영구자석 손실량 스케일링
    Wmag_scaled = Wmag_ref * speedScalingFactor;
end
