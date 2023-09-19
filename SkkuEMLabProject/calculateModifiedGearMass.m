function mg = calculateModifiedGearMass(n_P, n_g,n_P_base, ng_base, mg_base)
    fg_mass      =calcFactorGearMass(n_P, n_g)      ;
    fg_base_mass = calcFactorGearMass(n_P_base, ng_base) ;
    mg = (fg_mass / fg_base_mass) * mg_base;
end
