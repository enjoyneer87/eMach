%[text] Define ActiveXParameter
%[text] filter
%[text:tableOfContents]{"heading":"**목차**"} %[text:anchor:M_AC6A05D3]
%[text] 
function hybridACLossModelStr=devCalcMCADHybridACLoss(mcad)
%[text] %[text:anchor:H_27881829] ## get LAB ActiveXStr Variable
%[text] %[text:anchor:H_4BC10587] #### Define ActiveXParameter
ActiveXStr=loadMCadActiveXParameter();
ActiveXStr=ActiveXStr.ActiveXParametersStruct;
%[text] %[text:anchor:H_A19455C3] #### ACLossSpeedScalingMethod\_Lab - filter
n2ac_MotorLAB                   = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad,'n2ac_MotorLAB');
ACConductorLossSplit_Lab        = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad,'ACConductorLossSplit_Lab');
ACConductorLossProportion_Lab   = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad','ACConductorLossProportion_Lab');
ACLossSpeedScalingMethod_Lab    = getMCADTableValueFromActiveXstr(ActiveXStr, 'LossParameters_MotorLAB', mcad,'ACLossSpeedScalingMethod_Lab');
[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'AC');
filteredTable = filterMCADTable(filteredTable, 'FluxDensity');
filteredTable=getMcadTableVariable(filteredTable,mcad);

%% Proportion

switch length(ACConductorLossProportion_Lab.CurrentValue)
    case num2cell(2:100)  % ACConductorLossProportion_Lab.CurrentValue의 길이가 2 이상인 경우
        structArray = createStructArrayFromStringCellArray(ACConductorLossProportion_Lab.CurrentValue);
    case 1  % ACConductorLossProportion_Lab.CurrentValue의 길이가 정확히 1인 경우
        ACConductorLossProportion_Lab = convertCharTypeData2ArrayData(ACConductorLossProportion_Lab.CurrentValue{1});
    otherwise
        % 예외 처리: 길이가 0인 경우나 다른 경우에 대한 처리를 추가할 수 있습니다.
end

%P_alpha = (pi * l_a * d_c^4 * sigma * (omega * B)^2 / 64) * (1 / (1 + alpha * (T - T_0)));
%[text] %[text:anchor:H_EB2A4AB4] ### $&dollar&;\\mathrm{I}\_{\\mathrm{a}}&dollar&; is the active length of the conductors in metres\n&dollar&;d\_c&dollar&; is the diameter of round conductors in metres\n&dollar&;\\mathrm{h}\_{\\mathrm{c}}&dollar&; is the height of rectangular conductors in metres\n&dollar&;\\mathrm{w}\_{\\mathrm{c}}&dollar&; is the width of rectangular conductors in metres\n&dollar&;w&dollar&; is the electrical frequency\n&dollar&;B&dollar&; is the magnitude (peak) of the flux density in this slot region\n&dollar&;\\mathrm{T}&dollar&; is the winding temperature\n&dollar&;T\_0&dollar&; is the reference winding temperature\n&dollar&;\\delta&dollar&; is the electrical conducti\nvity of the conductor material\n&dollar&;\\alpha&dollar&; is the temperature coefficient of resistivity of the conductor material\n$
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
[~, Copper_Width]                  = mcad.GetVariable('Copper_Width');
[~, Copper_Height]                 = mcad.GetVariable('Copper_Height');
[~, lactive]                       = mcad.GetVariable('Stator_Lam_Length');
elec.T0.resistivity = 1.724E-8;  % 주어진 저항값 (옴·미터)
elec.T0.Conductivity = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
sigma=elec.T0.Conductivity;                      % [S/m]
elec.ACLoss.n2ac_MotorLAB = convertCharTypeData2ArrayData(n2ac_MotorLAB.CurrentValue{1});
% PolePair
[~, ShaftSpeed]    = mcad.GetVariable('ShaftSpeed');
[~, pole]          = mcad.GetVariable('Pole_Number');
polePair=double(pole)/2;
elec.ACLoss.omega_MotorLab  = rpm2OmegaE(elec.ACLoss.n2ac_MotorLAB,polePair);
omegaE                      = rpm2OmegaE(ShaftSpeed,polePair);
%[text] %[text:anchor:H_714BBB71] ## 
%[text] %[text:anchor:H_29A1DC16] ## Emag 한운전점 검증
%[text] %[text:anchor:H_59DF090F] ### OutputData - Magnetics
% SpeedList=[1000:1000:15000]
% skinDepth=calcSkinDepth(rpm2OmegaE(SpeedList,4));
% plot(SpeedList,skinDepth)
% B
matchingTable                   = getMCADTableValueFromActiveXstr(ActiveXStr, 'Magnetics', mcad,'FluxDensity','AC');
ArrayB      = convertCharTypeData2ArrayData(matchingTable.CurrentValue{1});
ArrayBLeft  = convertCharTypeData2ArrayData(matchingTable.CurrentValue{2});
ArrayBRight = convertCharTypeData2ArrayData(matchingTable.CurrentValue{3});
OutputDatabyMcad.ArrayB           = ArrayB     ; 
OutputDatabyMcad.ArrayBLeft       = ArrayBLeft ;     
OutputDatabyMcad.ArrayBRight      = ArrayBRight;         
% Alpha
[~, elec.alpha ]          = mcad.GetVariable('WindingAlpha_MotorLAB');
alpha=elec.alpha;
% Temperature
T0 = 20
T  = 20
% Slot Number
[~, slotNumber]          = mcad.GetVariable('Slot_Number');
slotNumber=double(slotNumber);
% HybridAdjustmentFactor_ACLosses 
[~, HybridAdjustmentFactor_ACLosses]          = mcad.GetVariable('HybridAdjustmentFactor_ACLosses');
% From Table
[filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'ACCon');  % Magnetics
getMagnetics=struct();
for idx = 1:length(filteredTable.AutomationName)
    fieldName = filteredTable.AutomationName{idx}; % 필드 이름 추출
    % fieldValue = filteredTable.CurrentValue{idx}; % 해당 필드의 값 추출    
    % 필드 이름에 공백 또는 부적합한 문자가 포함되어 있을 경우, MATLAB 필드 이름 규칙에 맞게 조정
    fieldName = matlab.lang.makeValidName(fieldName);    
    % 구조체에 필드와 값을 추가
    getMagnetics.(fieldName) = [];
end
getMagnetics=getMcadVariable(getMagnetics,mcad);

%% OutputData by Cuboid
OutputDatabyMcad.PacLeft          =    getMagnetics.ACConductorLoss_MagneticMethod_L   
OutputDatabyMcad.PacRight         =    getMagnetics.ACConductorLoss_MagneticMethod_R       
OutputDatabyMcad.Pac              =    getMagnetics.ACConductorLoss_MagneticMethod
%% OutputData
OutputDatabyMcad.PacMeanTotal     =    sum(getMagnetics.ACConductorLoss_MagneticMethod)
OutputDatabyMcad.PacTotalperCIdx  =    OutputDatabyMcad.PacMeanTotal
          
OutputDatabyMcad.pacTotalLeft     =    sum(getMagnetics.ACConductorLoss_MagneticMethod_L  )           
OutputDatabyMcad.pacTotalRight    =    sum(getMagnetics.ACConductorLoss_MagneticMethod_L  )            
OutputDatabyMcad.PacTotal         =    getMagnetics.ACConductorLoss_MagneticMethod_Total    
% end
OutputDatabyMcad = removeZeroRowsFromAllFields(OutputDatabyMcad);  %[W]
%%
%[text] %[text:anchor:H_D17F4642] ### OuputData의 단일 B값으로 계산
CuboidModel=struct();
CuboidModel.Winding_Cuboid_Width=[];
CuboidModel.Winding_Cuboid_Height=[];
CuboidModel.NumberOfCuboids=[];
CuboidModel=getMcadVariable(CuboidModel,mcad);
% Compare Cuboid and Copper
NumberOfCuboids      =CuboidModel.NumberOfCuboids;
Cuboid_Width         =unique(CuboidModel.Winding_Cuboid_Width);
Cuboid_Height        =unique(CuboidModel.Winding_Cuboid_Height);
Copper_Width;
Copper_Height;

for cIdx=1:NumberOfCuboids
    B=ArrayB(cIdx);
    Bleft=ArrayBLeft(cIdx);
    BRight=ArrayBRight(cIdx);
    %% stranded
    % divCoeffi=128;
    % PacLeft(cIdx)  = (mm2m(la)*mm2m(Copper_Width)*(mm2m(Copper_Height))^3 * sigma * (omegaE * Bleft)^2 / 12) * (1 / (1 + alpha * (T - T0)))*slotNumber/2*HybridAdjustmentFactor_ACLosses ;
    % PacRight(cIdx) = (mm2m(la)*mm2m(Copper_Width)*(mm2m(Copper_Height))^3 * sigma * (omegaE * BRight)^2 / 12) * (1 / (1 + alpha * (T - T0)))*slotNumber/2*HybridAdjustmentFactor_ACLosses ;
    % Pac(cIdx)      = (mm2m(la)*mm2m(Copper_Width)*(mm2m(Copper_Height))^3 * sigma * (omegaE * B)^2 / divCoeffi) * (1 / (1 + alpha * (T - T0)))*slotNumber*HybridAdjustmentFactor_ACLosses ;
    %% rectang
    divCoeffi=24;
    % *(1/ (1 + alpha * (T - T0)))*slotNumber/2*HybridAdjustmentFactor_ACLosses 
    % *(1/ (1 + alpha * (T - T0)))*slotNumber/2*HybridAdjustmentFactor_ACLosses 
    % *(1/ (1 + alpha * (T - T0)))*slotNumber  *HybridAdjustmentFactor_ACLosses 
    
%  calcHybridStrandProx1DMCAD로 대체할것 고려해보기
    OutputDatacalc.PacLeftFromB(cIdx,1)  =    (mm2m(lactive)*mm2m(Cuboid_Width)*(mm2m(Cuboid_Height))^3*sigma*(omegaE *Bleft )^2/divCoeffi) ;
    OutputDatacalc.PacRightFromB(cIdx,1) =    (mm2m(lactive)*mm2m(Cuboid_Width)*(mm2m(Cuboid_Height))^3*sigma*(omegaE *BRight)^2/divCoeffi) ;
    OutputDatacalc.PacFromB(cIdx,1)      =    (mm2m(lactive)*mm2m(Cuboid_Width)*(mm2m(Cuboid_Height))^3*sigma*(omegaE *B     )^2/divCoeffi) ;

end

%% Sum 4 Veri
OutputDatacalc.PacTotalperCIdx            =OutputDatacalc.PacLeftFromB+ OutputDatacalc.PacRightFromB;
OutputDatacalc.PacTotal                   =sum(OutputDatacalc.PacTotalperCIdx);
OutputDatacalc.pacTotalLeft               =sum(OutputDatacalc.PacLeftFromB);
OutputDatacalc.pacTotalRight              =sum(OutputDatacalc.PacRightFromB);
OutputDatacalc.PacMeanTotal               =sum(OutputDatacalc.PacFromB);
OutputDatacalc                            = removeZeroRowsFromAllFields(OutputDatacalc);
[~,CurrentMotFilePath_MotorLAB]=mcad.GetVariable('CurrentMotFilePath_MotorLAB');
%[text] %[text:anchor:H_17F60BF2] ### Graph 
%[text] %[text:anchor:H_0D93DE44] #### 가져오기
OpData                    =loadMCADSimulData(mcad); %[text:anchor:M_99C11B2F]
% B 재 플롯
% [~,NofConductor]=mcad.GetVariable('WindingLayers');
% NofConductor=double(NofConductor);
% ConductorNameListCell=mkNameListConductorB(NofConductor);
% DataNameList={};
% %%Check There is Same Type Figure
%     % figNumber=6;
%     % FigureData=checkExistFigure(figNumber);
%     % %%
%     % figure(figNumber)
%     % for CuIndex=1:2:(2*NofConductor-1)
%     %     subplot(2,2,(CuIndex+1)/2)
% Cuindex=7;
% opData.Wave.BCoductor{(CuIndex)}= plotMCADEmagCalc(ConductorNameListCell{CuIndex}, mcad,FigureData);
% % Name
% DataNameList{1}=strrep([ConductorNameListCell{CuIndex}],'FluxDensity','');
% % addName
% opData.Wave.BCoductor{(CuIndex)}.DataName         =DataNameList{1};
% hold on
% opData.Wave.BCoductor{(CuIndex+1)}= plotMCADEmagCalc(ConductorNameListCell{CuIndex+1}, mcad,FigureData);
% % Name
% DataNameList{2}=strrep([ConductorNameListCell{CuIndex+1}],'FluxDensity','');
% % addName
% opData.Wave.BCoductor{(CuIndex+1)}.DataName        =DataNameList{2};
% if strcmp(FigureData.PlotType,'Comparison')
%     DataNameList{3}=strrep([ConductorNameListCell{CuIndex}],'FluxDensity','');
%     DataNameList{4}=strrep([ConductorNameListCell{CuIndex+1}],'FluxDensity','');
% end
% legend(DataNameList);
% hold on
% 
% ResultStructEmagCalc=plotMCADEmagCalc(setGraphName, mcad,FigureData)
%%
%[text] %[text:anchor:H_F0E40E79] #### Graph AC 계산

%[text] %[text:anchor:H_A9DBEE54] #### Stranded
%[text] $P\_{\\alpha} = L\_a \\left( \\frac{\\pi d\_c^4 \\sigma (\\omega B)^2}{128} \\right) $ 2019 volpe
%[text] 2\*pi\*f =omega???
%[text] %[text:anchor:H_34F68F11] #### Rectangular
%[text] $P\_{ac} = \\left( L\_a\\frac{ w\_c h\_c^3 \\sigma (\\omega B)^2}{24} \\right) \n$  2019 volpe
%[text] ExpCalcHybridACLossModelwithSlotB
%[text] $&dollar&;\\mathrm{T}=\\frac{\\mathrm{V} \\cdot \\mathrm{s}}{\\mathrm{m}^2}&dollar&;$,$&dollar&;\\mathrm{T}=\\frac{\\mathrm{Wb}}{\\mathrm{m}^2}&dollar&;$
%[text] $&dollar&;&dollar&;\n\\frac{A\_e}{A}=\\frac{\\delta}{2 r}\n&dollar&;&dollar&;$
%[text] $A\_e$ is the effective conductor area (constrained by the skin effect).
%[text] $\\mathrm{A}$ is the total conductor area.
%[text] $\\bar{\\delta}$ is the skin depth.
%[text] $r$ is the conductor radius (or half the conductor height for rectangular conductors)
%[text] 개선된 방법은 피부 깊이가 번들 높이보다 현저히 낮은 경우 하이브리드 FEA AC 손실을 추가로 보정합니다.
% [filteredTable,categoryName] = findAutomationNameFromAllCategory(ActiveXStr, 'ACCon');
% ACConTable=getMcadTableVariable(filteredTable,mcad);
%[text] %[text:anchor:H_55BC648D] ## skin Depth
%[text] $&dollar&;\\rho&dollar&;$ :resistivity
%[text] $&dollar&;&dollar&;\n\\delta=\\sqrt{\\frac{2 p}{\\omega \\mu\_0}}\n&dollar&;&dollar&;$
%[text] where $\\rho$ is the conductor resistivity, $\\omega$ the angular frequency and $\\mu\_0$the permeability of free space.
%[text] 4*π*×10−7 (H/m)
%[text] 
%[text] 스킨 깊이가 도체 치수 $(\\delta\>h)$보다 큰 경우 전류 분포는 도체 단면에 걸쳐 거의 균일하며 스킨 효과를 무시할 수 있습니다. 이를 저항 제한 영역이라고 하며, 여기서 교류 손실은 방정식 $(1,2)$에 의해 주어진 대로 $f^2$에 비례합니다. 그러나 스킨 깊이가 도체 치수 $(\\delta\<h)$보다 작아지면 전류가 주로 도체 표면에서 흐르기 때문에 분포가 불균일해집니다. 이를 인덕턴스 제한 영역이라고 하며 스킨 효과가 크게 나타납니다. 이 영역에서 손실은 $f$에 비례하여 증가합니다.
%[text] 
elec.T0.resistivity = 1.724E-8;  % 주어진 저항값 (옴·미터)
elec.T0.Conductivity = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
sigma=elec.T0.Conductivity;                      % [S/m]
rho  = 1/sigma    ;  % resistivity (옴·미터)
mu0  = 4*pi*10^-7 ;      % [H/m]
SkinDepth_delta=sqrt((2*rho)/(omegaE*mu0))  ;     % [m]
SkinDepth_delta_inmm=m2mm(SkinDepth_delta)  ;
%[text] %[text:anchor:H_61F17075] ## 데이터 정리str
hybridACLossModelStr.OutputDatacalc               =OutputDatacalc;
hybridACLossModelStr.OutputDatabyMcad             =OutputDatabyMcad;
hybridACLossModelStr.getMcad            =getMagnetics;

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
hybridACLossModelStr.OpDataGraph=OpData;
hybridACLossModelStr.CuboidModel =CuboidModel;
end

%[appendix]{"version":"1.0"}
%---
