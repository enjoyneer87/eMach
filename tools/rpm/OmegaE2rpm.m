function rpm=OmegaE2rpm(omegaE,polePair)
  omega=elec2mech(omegaE,polePair);
  rpm=radsec2rpm(omega);
end