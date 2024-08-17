function hybridACLossModelStr=devCalcHybridACLossModelwithSlotB(mcad)
%% doNgetMCADLossPerSpeed에서 호출
% Define ActiveXParameter
%  filter
%% Define ActiveXParameter
ActiveXStr=loadMCadActiveXParameter();
ActiveXStr=ActiveXStr.ActiveXParametersStruct;
[~,CurrentMotFilePath_MotorLAB]=mcad.GetVariable('CurrentMotFilePath_MotorLAB');

%% filter
n2ac_MotorLAB                   = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad,'n2ac_MotorLAB');
ACConductorLossSplit_Lab        = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad,'ACConductorLossSplit_Lab');
ACConductorLossProportion_Lab   = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad','ACConductorLossProportion_Lab');
ACLossSpeedScalingMethod_Lab    = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad,'ACLossSpeedScalingMethod_Lab');


%% get All ActiveXStr Variable
[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'AC');
filteredTable = filterMCADTable(filteredTable, 'FluxDensity');
filteredTable=getMcadTableVariable(filteredTable,mcad);

%% switch
switch length(ACConductorLossProportion_Lab.CurrentValue)
    case num2cell(2:100)  % ACConductorLossProportion_Lab.CurrentValue의 길이가 2 이상인 경우
        structArray = createStructArrayFromStringCellArray(ACConductorLossProportion_Lab.CurrentValue);
    case 1  % ACConductorLossProportion_Lab.CurrentValue의 길이가 정확히 1인 경우
        ACConductorLossProportion_Lab = convertCharTypeData2ArrayData(ACConductorLossProportion_Lab.CurrentValue{1});
    otherwise
        % 예외 처리: 길이가 0인 경우나 다른 경우에 대한 처리를 추가할 수 있습니다.
end


%% if stranded
P_alpha = (pi * l_a * d_c^4 * sigma * (omega * B)^2 / 64) * (1 / (1 + alpha * (T - T_0)));

[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'ProximityLoss');


%% if HairPin
% la: m 단위의 길이
% wc: m 단위의 길이
% hc: m 단위의 길이
% sigma: 전기 저항도의 역수
% omega: 라디안/초 (rad/sec) 단위의 각속도
% B: 테슬라 (T) 단위의 자기장
% alpha: 상수
% T: 온도
% T0: 온도 상수

[~,la]            =mcad.GetVariable('Stator_Lam_Length')    ;        
[~,Copper_Width]  =mcad.GetVariable('Copper_Width')         ;
[~,Copper_Height] =mcad.GetVariable('Copper_Height')        ;    

 
elec.T0.resistivity    = 1.724E-8;  % 주어진 저항값 (옴·미터)
elec.T0.Conductivity   = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
sigma=elec.T0.Conductivity;
elec.ACLoss.n2ac_MotorLAB = convertCharTypeData2ArrayData(n2ac_MotorLAB.CurrentValue{1});

% PolePair
[~,PoleNumber] =mcad.GetVariable('Pole_Number')        ;    
polePair=double(PoleNumber/2);
% omegaE
elec.ACLoss.omega_MotorLab = rpm2OmegaE(elec.ACLoss.n2ac_MotorLAB,polePair);
[~,ShaftSpeed] =mcad.GetVariable('ShaftSpeed')        ;    
omegaE                      = rpm2OmegaE(ShaftSpeed,polePair);

%% B
matchingTable                   = getMCADTableValueFromActiveXstr(ActiveXStr, 'Magnetics', mcad,'FluxDensity','AC');
ArrayB           = convertCharTypeData2ArrayData(matchingTable.CurrentValue{1});
ArrayBLeft       = convertCharTypeData2ArrayData(matchingTable.CurrentValue{2});
ArrayBRight      = convertCharTypeData2ArrayData(matchingTable.CurrentValue{3});
hybridACLossModelStr.ArrayB           = ArrayB     ; 
hybridACLossModelStr.ArrayBLeft       = ArrayBLeft ;     
hybridACLossModelStr.ArrayBRight      = ArrayBRight;         
% Alpha
[~,elec.alpha] =mcad.GetVariable('WindingAlpha_MotorLAB')        ;    
alpha=elec.alpha;

% Temperature
T0= 20;
T = 20;
% Slot Number
[~,slotNumber]                      =mcad.GetVariable('Slot_Number')        ;    
% HybridAdjustmentFactor_ACLosses 
[~,HybridAdjustmentFactor_ACLosses] =mcad.GetVariable('HybridAdjustmentFactor_ACLosses')        ;    

%% [Table]P_ac 계산 - ArrayB는 도체마다 평균 자속밀도 
CuboidModel=struct();
CuboidModel.Winding_Cuboid_Width=[];
CuboidModel.Winding_Cuboid_Height=[];
CuboidModel.NumberOfCuboids=[];
CuboidModel=getMcadVariable(CuboidModel,mcad);
NumberOfCuboids =CuboidModel.NumberOfCuboids;
Cuboid_Width=unique(CuboidModel.Winding_Cuboid_Width);
Cuboid_Height=unique(CuboidModel.Winding_Cuboid_Height);

% Pac = (la * wc * hc^3 * sigma * (omega * B)^2 / 12) * (1 / (1 + alpha * (T - T0)));
% Omega가 있으니까 
for cIdx=1:NumberOfCuboids
    B     =ArrayB(cIdx);
    Bleft =ArrayBLeft(cIdx);
    BRight=ArrayBRight(cIdx);
    %% stranded
    % divCoeffi=128;
    % PacLeft(cIdx)  = (mm2m(la)*mm2m(Copper_Width)*(mm2m(Copper_Height))^3 * sigma * (omegaE * Bleft)^2 / 12) * (1 / (1 + alpha * (T - T0)))*slotNumber/2*HybridAdjustmentFactor_ACLosses ;
    % PacRight(cIdx) = (mm2m(la)*mm2m(Copper_Width)*(mm2m(Copper_Height))^3 * sigma * (omegaE * BRight)^2 / 12) * (1 / (1 + alpha * (T - T0)))*slotNumber/2*HybridAdjustmentFactor_ACLosses ;
    % Pac(cIdx)      = (mm2m(la)*mm2m(Copper_Width)*(mm2m(Copper_Height))^3 * sigma * (omegaE * B)^2 / divCoeffi) * (1 / (1 + alpha * (T - T0)))*slotNumber*HybridAdjustmentFactor_ACLosses ;
    %% rectang
    divCoeffi=24;

    % 식 1
    calc.PacLeftFromB(cIdx,1)  =    (mm2m(la)*mm2m(Cuboid_Width)*(mm2m(Cuboid_Height))^3*sigma*(omegaE *Bleft )^2/divCoeffi) ;
    calc.PacRightFromB(cIdx,1) =    (mm2m(la)*mm2m(Cuboid_Width)*(mm2m(Cuboid_Height))^3*sigma*(omegaE *BRight)^2/divCoeffi) ;
    calc.PacFromB(cIdx,1)      =    (mm2m(la)*mm2m(Cuboid_Width)*(mm2m(Cuboid_Height))^3*sigma*(omegaE *B     )^2/divCoeffi) ;
    % 식 2
    PacLeft(cIdx)              = (mm2m(la) * mm2m(Copper_Width) * (mm2m(Copper_Height))^3 * sigma * (omegaE * Bleft)^2 / 12) * (1 / (1 + alpha * (T - T0)))*slotNumber/2*HybridAdjustmentFactor_ACLosses ;
    PacRight(cIdx)             = (mm2m(la) * mm2m(Copper_Width) * (mm2m(Copper_Height))^3 * sigma * (omegaE * BRight)^2 / 12) * (1 / (1 + alpha * (T - T0)))*slotNumber/2*HybridAdjustmentFactor_ACLosses ;
    Pac(cIdx)                  = (mm2m(la) * mm2m(Copper_Width) * (mm2m(Copper_Height))^3 * sigma * (omegaE * B)^2 / 12) * (1 / (1 + alpha * (T - T0)))*slotNumber*HybridAdjustmentFactor_ACLosses ;
end
%% Sum
calc.PacTotalperCIdx=(calc.PacLeftFromB+ calc.PacRightFromB)/2;
calc.PacTotal     =sum(calc.PacTotalperCIdx);
calc.pacTotalLeft =sum(calc.PacLeftFromB);
calc.pacTotalRight=sum(calc.PacRightFromB);
calc.PacMeanTotal =sum(calc.PacFromB);
calc = removeZeroRowsFromAllFields(calc);

%% Sum
PacTotalperCIdx=PacLeft+PacRight;
pacTotalLeft=sum(PacLeft);
pacTotalRight=sum(PacRight);
PacTotal=sum(PacTotalperCIdx);

[~,CurrentMotFilePath_MotorLAB]=mcad.GetVariable('CurrentMotFilePath_MotorLAB');
%% For Comparison
% From Table
[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'ACCon');
%%
getMcad=struct();
for idx = 1:length(filteredTable.AutomationName)
    fieldName = filteredTable.AutomationName{idx}; % 필드 이름 추출
    % fieldValue = filteredTable.CurrentValue{idx}; % 해당 필드의 값 추출    
    % 필드 이름에 공백 또는 부적합한 문자가 포함되어 있을 경우, MATLAB 필드 이름 규칙에 맞게 조정
    fieldName = matlab.lang.makeValidName(fieldName);    
    % 구조체에 필드와 값을 추가
    getMcad.(fieldName) = [];
end

getMcad=getMcadVariable(getMcad,mcad) %[W]
%% getMcad -> byMcad
byMcad.PacLeft          =    getMcad.ACConductorLoss_MagneticMethod_L   
byMcad.PacRight         =    getMcad.ACConductorLoss_MagneticMethod_R       
byMcad.Pac              =    getMcad.ACConductorLoss_MagneticMethod
byMcad.PacMeanTotal     =    sum(getMcad.ACConductorLoss_MagneticMethod)
byMcad.PacTotalperCIdx  =    byMcad.PacMeanTotal
          
byMcad.pacTotalLeft     =    sum(getMcad.ACConductorLoss_MagneticMethod_L  )           
byMcad.pacTotalRight    =    sum(getMcad.ACConductorLoss_MagneticMethod_L  )            
byMcad.PacTotal         =    getMcad.ACConductorLoss_MagneticMethod_Total    
% end
byMcad = removeZeroRowsFromAllFields(byMcad);
%% WaveForm으로 계산

%%
% [filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'ACCon');
% ACConTable                   =getMcadTableVariable(filteredTable,mcad);
%% 정리 str
hybridACLossModelStr.calc               =calc;
hybridACLossModelStr.byMcad             =byMcad;   %[W]
hybridACLossModelStr.getMcad            =getMcad;  %[W]

% hybridACLossModelStr.ACConTable=ACConTable;
hybridACLossModelStr.CurrentMotFilePath_MotorLAB=CurrentMotFilePath_MotorLAB;
% rpm
hybridACLossModelStr.LabRPM=elec.ACLoss.n2ac_MotorLAB;
hybridACLossModelStr.MagShaftSpeed=ShaftSpeed;
% SimulCondition
% Mag
[~,ArmatureConductor_Temperature]=mcad.GetVariable('ArmatureConductor_Temperature') ;                        
[~,Magnet_Temperature]           =mcad.GetVariable('Magnet_Temperature')            ;            
[~,PeakCurrent]                  =mcad.GetVariable('PeakCurrent')                   ;    
[~,PhaseAdvance]                 =mcad.GetVariable('PhaseAdvance')                  ;    

hybridACLossModelStr.ArmatureConductor_Temperature =ArmatureConductor_Temperature;
hybridACLossModelStr.Magnet_Temperature            =Magnet_Temperature;
hybridACLossModelStr.PeakCurrent =PeakCurrent;
hybridACLossModelStr.PhaseAdvance=PhaseAdvance;

end