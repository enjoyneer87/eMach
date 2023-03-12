function dataobj=compMatFilePsi(dataobj)
%COMPMATFILE 이 함수의 요약 설명 위치
%   자세한 설명 위치
matData=dataobj.MotorcadMat
matData.calcType

idVec=matData.Id_Peak(:,1);
iqVec=matData.Iq_Peak(1,:);

matData.Stator_Current_Line_Peak
matData.Phase_Advance
size(matData.Stator_Current_Line_Peak)
size(matData.Phase_Advance)

currentVec=matData.Stator_Current_Line_Peak(:,1); % column sort
size(currentVec)
phaseVec=matData.Phase_Advance(1,:); % row sort
size(phaseVec)

flux1D=matData.Flux_Linkage_D;
flux1Q=matData.Flux_Linkage_Q
size(flux1D)

dataobj.flux_linkage_map.in_d = flux1D;
dataobj.flux_linkage_map.in_q = flux1Q;

dataobj.currentVec=currentVec;
dataobj.phaseVec=phaseVec;
end

