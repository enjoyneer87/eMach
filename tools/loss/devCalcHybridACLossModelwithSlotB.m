function hybridACLossModelStr=devCalcHybridACLossModelwithSlotB(mcad)
%% Define ActiveXParameter
ActiveXStr=loadMCadActiveXParameter();
ActiveXStr=ActiveXStr.ActiveXParametersStruct;
% filter
matchingTable = getMCADTableValueFromActiveXstr(ActiveXStr, 'Magnetics', mcad,'FluxDensity','AC');
n2ac_MotorLAB                   = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad,'n2ac_MotorLAB');
ACConductorLossSplit_Lab        = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad,'ACConductorLossSplit_Lab');
ACConductorLossProportion_Lab   = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad','ACConductorLossProportion_Lab');
ACLossSpeedScalingMethod_Lab    = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad,'ACLossSpeedScalingMethod_Lab');





[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'AC');
filteredTable = filterMCADTable(filteredTable, 'FluxDensity');
filteredTable=getMcadTableVariable(filteredTable,mcad);

switch length(ACConductorLossProportion_Lab.CurrentValue)
    case num2cell(2:100)  % ACConductorLossProportion_Lab.CurrentValue의 길이가 2 이상인 경우
        structArray = createStructArrayFromStringCellArray(ACConductorLossProportion_Lab.CurrentValue);
    case 1  % ACConductorLossProportion_Lab.CurrentValue의 길이가 정확히 1인 경우
        ACConductorLossProportion_Lab = convertCharTypeData2ArrayData(ACConductorLossProportion_Lab.CurrentValue{1});
    otherwise
        % 예외 처리: 길이가 0인 경우나 다른 경우에 대한 처리를 추가할 수 있습니다.
end


%% if stranded
% % P_alpha = (pi * l_a * d_c^4 * sigma * (omega * B)^2 / 64) * (1 / (1 + alpha * (T - T_0)));
% $\mathrm{I}_{\mathrm{a}}$ is the active length of the conductors in metres
% $d_c$ is the diameter of round conductors in metres
% $\mathrm{h}_{\mathrm{c}}$ is the height of rectangular conductors in metres
% $\mathrm{w}_{\mathrm{c}}$ is the width of rectangular conductors in metres
% $w$ is the electrical frequency
% $B$ is the magnitude (peak) of the flux density in this slot region
% $\mathrm{T}$ is the winding temperature
% $T_0$ is the reference winding temperature
% $\delta$ is the electrical conductivity of the conductor material
% $\alpha$ is the temperature coefficient of resistivity of the conductor material

[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'ProximityLoss');


% if HairPin
% la: m 단위의 길이
% wc: m 단위의 길이
% hc: m 단위의 길이
% sigma: 전기 저항도의 역수
% omega: 라디안/초 (rad/sec) 단위의 각속도
% B: 테슬라 (T) 단위의 자기장
% alpha: 상수
% T: 온도
% T0: 온도 상수

[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'Stator_Lam_Length');
filteredTable=getMcadTableVariable(filteredTable,mcad);
la=convertCharTypeData2ArrayData(filteredTable.CurrentValue{1});

[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'Copper_Width');
filteredTable=getMcadTableVariable(filteredTable,mcad);
Copper_Width=convertCharTypeData2ArrayData(filteredTable.CurrentValue{1});

[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'Copper_Height');
filteredTable=getMcadTableVariable(filteredTable,mcad);
Copper_Height=convertCharTypeData2ArrayData(filteredTable.CurrentValue{1});

 
elec.T0.resistivity = 1.724E-8;  % 주어진 저항값 (옴·미터)
elec.T0.Conductivity = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
sigma=elec.T0.Conductivity;


% [filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'Freq');
% filteredTable = filterMCADTable(filteredTable, 'Ac');
elec.ACLoss.n2ac_MotorLAB = convertCharTypeData2ArrayData(n2ac_MotorLAB.CurrentValue{1});

% PolePair
[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'Pole_');
filteredTable = filterMCADTable(filteredTable, 'Number');
polePair=filteredTable.CurrentValue{2}/2;
elec.ACLoss.omega_MotorLab = rpm2OmegaE(elec.ACLoss.n2ac_MotorLAB,polePair);
omegaE = rpm2OmegaE(5100,4)
% B
ArrayB = convertCharTypeData2ArrayData(matchingTable.CurrentValue{1});
ArrayBLeft = convertCharTypeData2ArrayData(matchingTable.CurrentValue{2});
ArrayBRight = convertCharTypeData2ArrayData(matchingTable.CurrentValue{3});
hybridACLossModelStr.ArrayB           = ArrayB     ; 
hybridACLossModelStr.ArrayBLeft       = ArrayBLeft ;     
hybridACLossModelStr.ArrayBRight      = ArrayBRight;         
% Alpha
[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'WindingAlpha_MotorLAB');
filteredTable=getMcadTableVariable(filteredTable,mcad);
elec.alpha = convertCharTypeData2ArrayData(filteredTable.CurrentValue{1});
alpha=elec.alpha;

% Temperature
T0 =20
T= 20
% Slot Number
[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'Slot_Number');
filteredTable=getMcadTableVariable(filteredTable,mcad);
slotNumber = convertCharTypeData2ArrayData(filteredTable.CurrentValue{1});

% HybridAdjustmentFactor_ACLosses 
[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'HybridAdjustmentFactor_ACLosses');
filteredTable=getMcadTableVariable(filteredTable,mcad);
HybridAdjustmentFactor_ACLosses = convertCharTypeData2ArrayData(filteredTable.CurrentValue{1});

%% P_ac 계산
% Pac = (la * wc * hc^3 * sigma * (omega * B)^2 / 12) * (1 / (1 + alpha * (T - T0)));

for cIdx=1:10
    B=ArrayB(cIdx);
    Bleft=ArrayBLeft(cIdx);
    BRight=ArrayBRight(cIdx);
    PacLeft(cIdx) = (mm2m(la) * mm2m(Copper_Width) * (mm2m(Copper_Height))^3 * sigma * (omegaE * Bleft)^2 / 12) * (1 / (1 + alpha * (T - T0)))*slotNumber/2*HybridAdjustmentFactor_ACLosses ;
    PacRight(cIdx) = (mm2m(la) * mm2m(Copper_Width) * (mm2m(Copper_Height))^3 * sigma * (omegaE * BRight)^2 / 12) * (1 / (1 + alpha * (T - T0)))*slotNumber/2*HybridAdjustmentFactor_ACLosses ;
    Pac(cIdx) = (mm2m(la) * mm2m(Copper_Width) * (mm2m(Copper_Height))^3 * sigma * (omegaE * B)^2 / 12) * (1 / (1 + alpha * (T - T0)))*slotNumber*HybridAdjustmentFactor_ACLosses ;
end

PacTotalperCIdx=PacLeft+PacRight;
pacTotalLeft=sum(PacLeft);
pacTotalRight=sum(PacRight);
PacTotal=sum(PacTotalperCIdx);

[~,CurrentMotFilePath_MotorLAB]=mcad.GetVariable('CurrentMotFilePath_MotorLAB');
%% For Comparison
[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'ACCon');
ACConTable=getMcadTableVariable(filteredTable,mcad);
%% str
hybridACLossModelStr.PacTotal=PacTotal;
hybridACLossModelStr.ACConTable=ACConTable;
hybridACLossModelStr.CurrentMotFilePath_MotorLAB=CurrentMotFilePath_MotorLAB;

end