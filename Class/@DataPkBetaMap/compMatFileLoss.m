function dataobj=compMatFileLoss(dataobj)
%COMPMATFILE 이 함수의 요약 설명 위치
%   자세한 설명 위치
%% dataobj : DataPkBetaMap obj
matData=dataobj.MotorcadMat;
matData.calcType;

idVec=matData.Id_Peak(:,1);
iqVec=matData.Iq_Peak(1,:);

matData.Stator_Current_Line_Peak;
matData.Phase_Advance;
size(matData.Stator_Current_Line_Peak);
size(matData.Phase_Advance);


%% Add CurrentVec and phaseVec
currentVec=matData.Stator_Current_Line_Peak(:,1); % column sort
size(currentVec);
phaseVec=matData.Phase_Advance(1,:); % row sort
size(phaseVec);

dataobj.currentVec=currentVec;
dataobj.phaseVec=phaseVec;

%% Hysteresis Coefficeint 
HysCoeff=HysCoefficientData(matData);


%% Eddy Coefficeint
EddyCoeff=EddyCoefficientData(matData);

%% Add HysCoeff and EddyCoeff to LossMap property
dataobj.LossMap.HysCoeff = HysCoeff;
dataobj.LossMap.EddyCoeff = EddyCoeff;

end

