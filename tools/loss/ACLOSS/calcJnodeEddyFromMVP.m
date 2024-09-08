function Jeddy = calcJnodeEddyFromMVP(A_fieldFP, timeStep,sigma)
    
    %% dev
    % calculateTimeDerivative - 전기 전도도와 벡터 포텐셜의 시간 변화율 계산
    % timeStep=endtime/120
    % size(A_fieldFP);
    %
    % 입력 매개변수:
    %   sigma - 전기 전도도(상수 또는 함수)
    %   A - 벡터 포텐셜 함수 (시간의 함수)
    %   time - 시간 값 (벡터 또는 스칼라)
    %
    % 출력:
    %   dA_dt - sigma * dA/dt 값 (시간에 따른 변화)
    if nargin<3
    resitivitityMCAD=1.724E-08;
    sigmaMCAD=1/resitivitityMCAD;
    rhoJmag=1.673e-08;
    sigmaJMAG=1/rhoJmag;
    sigma=sigmaJMAG;
    end
    % 벡터 포텐셜의 시간에 따른 변화율 (dA/dt)
    dA_dt = gradient(A_fieldFP,timeStep);
    
    %%

    % σ * (dA/dt) 계산
    Jeddy = sigma .* dA_dt;




end
