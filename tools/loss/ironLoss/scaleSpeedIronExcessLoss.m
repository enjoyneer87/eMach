function WIronExcess_Scaled = scaleSpeedIronExcessLoss(WIronExcess_ref, fBuild, fOp)
    % 입력 매개변수 설명:
    % WFe_ref: 참조 철손 값 (Id, Iq에 따른 초기 철손 값)
    % fBuild: 참조 주파수 (빌드 주파수)
    % fOp: 운전 주파수 (목표 주파수)

    % 주파수 변화에 따른 철손 스케일링
    ExponentScaleFactor=3/2;
    scalingFactor = (fOp / fBuild)^ExponentScaleFactor; % 주파수에 따른 철손은 주파수의 제곱에 비례한다고 가정

    % 스케일링된 철손 값 계산
    WIronExcess_Scaled = WIronExcess_ref * scalingFactor;
end
