function tempScalingFactor=createTempScalingFactor(Tcalc,Tref,alpha)
    tempScalingFactor=1/(1+alpha*(Tcalc-Tref));
end