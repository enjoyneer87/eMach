function ConductorNameListCell=mkNameListConductorB(NofConductor)

ConductorNameListCell={};
% NofConductor=4

for ConductorIndex=1:NofConductor
    LeftConductorNameStr=['ConductorFluxDensity_L_',num2str(ConductorIndex)];
   RightConductorNameStr=['ConductorFluxDensity_R_',num2str(ConductorIndex)];
    ConductorNameListCell=[ConductorNameListCell;{LeftConductorNameStr;RightConductorNameStr}]
end

end