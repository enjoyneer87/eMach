function fg_mass = calcFactorGearMass(n_P, n_g)
    fg_mass = 1/n_P + 1/(n_P * ((n_g - 2)/2)) + ((n_g - 2)/2) + ((n_g - 2)/2)^2 + (0.4 * (n_g - 1)^2) / (n_P * ((n_g - 2)/2));
end
