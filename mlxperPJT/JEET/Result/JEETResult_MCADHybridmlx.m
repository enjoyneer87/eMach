
totalNumberMcad=1
for i=1:totalNumberMcad
    mcad(i)=actxserver('motorcad.appautomation');
end
mcad=callMCAD(1)
%% 1. [WIP] Single Point AC Hybrid Method Verification -2ea

% refPath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\e10_UserRemesh.mot';
refPath='F:\KDH\Thesis\JEET\e10\refModel\e10_UserRemesh.mot'
mcad.LoadFromFile(refPath)
%% 
% 2.[Done4MCAD]Improved Method vs Original Method
% 
%% 
% * originally VeriCalcHybridACLossModelwithSlotB.mlx mcad Part
%% 
% Hybrid AC Loss Method
% 
% Hairpin AC loss location Method
% 
% hybrid AC Loss High Frequency Scaling Correction Method

% Hybrid Method 3媛?% Detail Method 1媛? 
% ?띾룄 由ъ뒪??speedList=[500, 1000 ,2000,4000,8000,15000]
% 紐⑤뱺 寃쎌슦???섏뿉 ???寃곌낵瑜???ν븷 援ъ“泥?諛곗뿴 珥덇린??% 寃쎌슦??????speedList=[8000]
tic 
% 媛?硫붿냼?쒖뿉 ????ㅼ젙 (0: Original, 1: Improved)
for caseIndex=1:1
HybridSetting           =mkMCADHybridACMethodCase(caseIndex)
MCADResultSet(caseIndex)=doNgetMCADLossPerSpeed(mcad,speedList,HybridSetting);
end
%     end
% end
toc
% [WIP] rev1 Computation with Hybrid Method From MCAD ?곗씠?? Single Point B Plot Graph
% calcHybridACConductorLoss
% 
% calcHybridStrandProx1D
% 
% calcHybridStrandProx1DMCAD
% 
% 

mcad(1).DoMagneticCalculation;

SimulationSmall=loadMCADSimulData(mcad(1))
SimulationSmall.ShaftSpeed=5000
SimulationSmall.pole=8
freqE=rpm2freqE(5000,4)
conductorType='rectangular'

McadIndex=1
[~, Copper_Width]    = mcad(McadIndex).GetVariable('Copper_Width');
[~, Copper_Height]   = mcad(McadIndex).GetVariable('Copper_Height');
[~, Stator_Lam_Length]              = mcad(McadIndex).GetVariable('Stator_Lam_Length');
dimensions=[Copper_Width,Copper_Height]
lactive=Stator_Lam_Length

SimulationSmall=simulationResults(1).SimulationSmall(6)
for conductorIndex=1:4
figure(conductorIndex)
Bm=SimulationSmall.Wave(conductorIndex).BCoductor.dataTable.GraphValue
% P_loss = calcHybridACConductorLoss(conductorType, dimensions, freqE, B_r, B_theta_m, l,sigma, mu_c)
% P_rect = calcHybridStrandProx1D(gamma_w(1), gamma_h(1), mu0, sigma, lactive/1000, Bm)
% P_rect_prime  = calcHybridStrandProx1D(gamma_w_prime(1), gamma_h_prime(1), mu0, sigma, lactive/1000, Bm)  %[W]
% P_rect_prime2 = calcHybridStrandProx1D(gamma_w_prime(1), gamma_h_prime_w(1), mu0, sigma, lactive/1000, Bm)  %[W]
% P_rectMCAD1D  = calcHybridStrandProx1DMCAD(w, h, sigma, freqE,lactive/1000, Bm)
P_rect          = calcHybridStrandProx1D(gamma_w(1), gamma_h(1), mu0, sigma, lactive/1000, Bm)  %[W]
P_rectImproved  = calcHybridStrandProxImproved1D(gamma_w(1), gamma_h(1), mu0, sigma, lactive/1000, Bm)  %[W]
% P_rect_12     = calcHybridStrandProx1D(gamma_w(1), gamma_h(1), mu0, sigma, lactive/1000/2, Bm)  %[W]
plot(SimulationSmall.Wave(conductorIndex).BCoductor.dataTable(:,1).Variables,P_rect,'b')
hold on
% plot(SimulationSmall.Wave(conductorIndex).BCoductor.dataTable(:,1).Variables,P_rect_12,'--')
plot(SimulationSmall.Wave(conductorIndex).BCoductor.dataTable(:,1).Variables,P_rectImproved,'--')
% plot(SimulationSmall.Wave(conductorIndex).BCoductor.dataTable(:,1).Variables,P_rect_prime,'b')
% plot(SimulationSmall.Wave(conductorIndex).BCoductor.dataTable(:,1).Variables,P_rect_prime2,'k')
% P_rectMCAD=SimulationSmall.Wave(conductorIndex).ACLossCoductor.dataTable(:,2).Variables
% hold on
% ratio=P_rectMCAD./P_rect
% rms(P_rect)
% rms(P_rectMCAD)
% plot(SimulationSmall.Wave(1).BCoductor.dataTable(:,1).Variables,ratio,'b')
hold on
plot(SimulationSmall.Wave(conductorIndex).ACLossCoductor.dataTable(:,1).Variables,SimulationSmall.Wave(conductorIndex).ACLossCoductor.dataTable.GraphValue/1000,'--')
end

% Arrayfun 議고쉶 

% simulationResults 援ъ“泥?諛곗뿴 ?덉떆
% simulationResults = struct('Speed', {1000, 2000, 3000, 1000}, 'Method', {'Method1', 'Method2', 'Method1', 'Method2'}, ...);

% 議고쉶?섍퀬???섎뒗 ?띾룄 媛?targetSpeed = 1000;

% ?띾룄媛 targetSpeed? ?쇱튂?섎뒗吏 ?щ?瑜??먮퀎?섏뿬 ?쇰━??諛곗뿴 ?앹꽦
isTargetSpeed = arrayfun(@(x) x.Speed == targetSpeed, simulationResults)

% ?쇰━???몃뜳?깆쓣 ?ъ슜?섏뿬 ?대떦 ?띾룄??寃곌낵留??꾪꽣留?filteredResults = simulationResults(isTargetSpeed);

% ?꾪꽣留곷맂 寃곌낵 異쒕젰
disp(filteredResults);



% ?꾪꽣留?議곌굔: ACLossHighFrequencyScaling_Method, HairpinACLossLocationMethod, HybridACLossMethod 紐⑤몢 1
filteredResults = simulationResults(arrayfun(@(x) ...
    x.ACLossHighFrequencyScaling_Method == 1 && ...
    x.HairpinACLossLocationMethod ==  1&& ...
    x.HybridACLossMethod == 1, ...
    simulationResults));


% filteredResults 援ъ“泥?諛곗뿴?먯꽌 PacTotal 媛?異붿텧
Speed                = arrayfun(@(x) x.Speed, filteredResults);
PacByMcadTotalValues = arrayfun(@(x) x.CalcedhybridACLoss.byMcad.PacTotal, filteredResults);
PacCalcTotalValues   = arrayfun(@(x) x.CalcedhybridACLoss.calc.PacTotal, filteredResults);

% save("KDHPC2024WorkSpace4ACLossCompMCAD.mat","PacCalcTotalValues","PacByMcadTotalValues","Speed","simulationResults","hybridACLossPerRPM","PacByMcadTotalValuesScale","PacCalcTotalValuesScale")

% Plot

% PacTotal 媛믪뿉 ???洹몃옒??洹몃━湲?plot(Speed,PacByMcadTotalValues);
xlabel('Index'); % ?몃뜳???먮뒗 ?ㅻⅨ ?곸젅???쇰꺼
ylabel('PacTotal'); % ?곸젅???⑥쐞瑜??ы븿???쇰꺼
title('PacTotal Values from filteredResults');
grid on;

figure(2)
plot(Speed,PacCalcTotalValues);
xlabel('Index');             % ?몃뜳???먮뒗 ?ㅻⅨ ?곸젅???쇰꺼
ylabel('PacCalcTotal');      % ?곸젅???⑥쐞瑜??ы븿???쇰꺼
title('PacTotal Values from filteredResults');
grid on;

%% 
% 鍮꾩쑉 鍮꾧탳
%% 
% * ?띾룄 4諛곗뵫 (?쒓낢鍮? ?뺤씤
% * 

% ?띾룄蹂?李⑥씠
index=1
divRatio=[]
for i=length(PacCalcTotalValues):-1:2
divRatio(index)=PacCalcTotalValues(i)./PacCalcTotalValues(i-1)
index=index+1
end

%% Calc? MCAD李⑥씠 鍮꾩쑉
RatioCalc4Model.Model1.value=PacByMcadTotalValues/1000./PacCalcTotalValues
RatioCalc4Model.Model2.value=PacByMcadTotalValuesScale/1000./PacCalcTotalValuesScale
RatioCalc4Model.Model3.value=PacByMcadTotalValuesScale/1000./PacCalcTotalValuesScale

[~,RatioCalc4Model.Model1.Path]=mcad(1).GetVariable("CurrentMotFilePath_MotorLAB")
[~,RatioCalc4Model.Model2.Path]=mcad(2).GetVariable("CurrentMotFilePath_MotorLAB")
[~,RatioCalc4Model.Model3.Path]=mcad(3).GetVariable("CurrentMotFilePath_MotorLAB")
