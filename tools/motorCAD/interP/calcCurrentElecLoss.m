function ElecLossBranchData = calcCurrentElecLoss(lambdaD, lambdaQ, Power_PostLoss, Torque_PostLoss, omegaE)
    % 전력 손실에서 전기적 손실을 계산
    PelecLoss = Power_PostLoss;

    % 전기적 RMS 전류 계산
    iqsRMS = (PelecLoss * lambdaQ) / (omegaE * (lambdaD + lambdaQ)^2);
    isRMS = sqrt(PelecLoss * iqsRMS / (omegaE * lambdaQ));
    idsRMS = lambdaD / lambdaQ * iqsRMS;

    % 전기적 저항 계산
    RelecLoss = PelecLoss / (isRMS^2);

    % pk 전류 계산
    ispk = rms2pk(isRMS);

    % 결과 데이터 구조 생성
    ElecLossBranchData.ispk = ispk;
    ElecLossBranchData.idsRMS = idsRMS;
    ElecLossBranchData.iqsRMS = iqsRMS;
    ElecLossBranchData.RelecLoss = RelecLoss;
    ElecLossBranchData.omegaE = omegaE;
    ElecLossBranchData.PelecLossWODCLoss=PelecLoss;
    ElecLossBranchData.TorqueElecLossWODCLoss=Torque_PostLoss;
end