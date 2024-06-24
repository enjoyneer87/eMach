function ArmatureConductorCSA=calcConductorCSAFromJ(Irms,ParallelPath,Nstrand,Jrms)
    ArmatureConductorCSA = Irms / (Jrms * ParallelPath * Nstrand);
  
end