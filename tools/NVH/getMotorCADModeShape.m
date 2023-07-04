mcad = actxserver('MotorCAD.AppAutomation');
NumGraphPoints=361
LumpK=zeros(NumGraphPoints,1)
LumpM=zeros(NumGraphPoints,1)
NaturalFreq=zeros(NumGraphPoints,1)


% setGraphName{dataIndex}
setGraphName={'NVH_LumpedStiffness','NVH_LumpedMass','NVH_NaturalFrequency'}
% Lumped Stiffness      
for loop = 0:NumGraphPoints
    [success,x,y1] = mcad.GetMagneticGraphPoint(setGraphName{1}, loop);    
    [success,x,y2] = mcad.GetMagneticGraphPoint(setGraphName{2}, loop);    
    [success,x,y3] = mcad.GetMagneticGraphPoint(setGraphName{3}, loop);    
    if success == 0
        ModeNumber(loop+1) = x;
        LumpK(loop+1) = y1;  %[MN/m]
        LumpM(loop+1) = y2;
        NaturalFreq(loop+1) = y3;
    end
end


NVH_ModeData=struct();
NVH_ModeData.NumGraphPoints=NumGraphPoints;
NVH_ModeData.LumpK=LumpK
NVH_ModeData.LumpM=LumpM
NVH_ModeData.NaturalFreq=NaturalFreq
