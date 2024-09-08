function DCLoss1Ph=calcDCLossByJ(JrmsinMsqr,OneSlotArea,Lactive,slots,FilFactor,rho)
    % NSPP=calcNSPP(slots,pole);
    % InNOut=2;
    % parallelNumbe
    PhaseNumber=3;
    DCLoss1Ph=calcJLoss(JrmsinMsqr, OneSlotArea*mm2m(Lactive), rho)*slots/FilFactor/PhaseNumber;
end