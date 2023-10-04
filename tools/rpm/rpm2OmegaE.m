function omegaE=rpm2OmegaE(rpm,polePair)
   omega=rpm2radsec(rpm);
   omegaE=mech2elec(omega,polePair);
end