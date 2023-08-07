function variable=getFundamentalBEMF(variable,mcad)

    SpeedBEMF = variable.SpeedBEMF;
    
    [Success,NoloadPsiD] = mcad.GetArrayVariable ('PsiDModel_Lab',0);% [Vs] Unit  
    [Success,NoloadPsiQ] = mcad.GetArrayVariable ('PsiQModel_Lab',0); % [Vs] Unit  
    
    [Success,p] = mcad.GetVariable('Pole_Number');
    Wr_test = 2 * pi * SpeedBEMF / 60 *p / 2;  
    BEMF_D=Wr_test*NoloadPsiD;
    BEMF_Q=Wr_test*NoloadPsiQ;
    phaseEmfFund=sqrt(BEMF_D^2+BEMF_Q^2);
    LineEmfFund=phaseEmfFund*sqrt(3);
    LineEmfFund=variable.scaleCoeff*LineEmfFund;

end