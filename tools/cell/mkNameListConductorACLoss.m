function ConductorNameListCell=mkNameListConductorACLoss(NofConductor)

ConductorNameListCell={};
% NofConductor=4

for ConductorIndex=1:NofConductor
    LeftConductorNameStr  =['ACConductorLoss_L_',num2str(ConductorIndex)];
    RightConductorNameStr =['ACConductorLoss_R_',num2str(ConductorIndex)];
    ConductorNameListCell=[ConductorNameListCell;{LeftConductorNameStr;RightConductorNameStr}];
end

end