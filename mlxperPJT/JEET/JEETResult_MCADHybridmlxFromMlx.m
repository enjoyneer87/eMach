
totalNumberMcad=2
for i=1:totalNumberMcad
    mcad(i)=actxserver('motorcad.appautomation');
end

%% 1. [WIP] Single Point AC Hybrid Method Verification -2ea

refPath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\e10_UserRemesh.mot';
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

% Hybrid Method 3개
% Detail Method 1개? 
% 속도 리스트
speedList=[500, 1000 ,2000,4000,8000,15000]
% 모든 경우의 수에 대한 결과를 저장할 구조체 배열 초기화
% 경우의 수 인
speedList=[8000]
tic 
% 각 메소드에 대한 설정 (0: Original, 1: Improved)
for caseIndex=1:1
HybridSetting           =mkMCADHybridACMethodCase(caseIndex)
MCADResultSet(caseIndex)=doNgetMCADLossPerSpeed(mcad,speedList,HybridSetting);
end
%     end
% end
toc
% [WIP] rev1 Computation with Hybrid Method From MCAD 데이터, Single Point B Plot Graph
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

% Arrayfun 조회 

% simulationResults 구조체 배열 예시
% simulationResults = struct('Speed', {1000, 2000, 3000, 1000}, 'Method', {'Method1', 'Method2', 'Method1', 'Method2'}, ...);

% 조회하고자 하는 속도 값
targetSpeed = 1000;

% 속도가 targetSpeed와 일치하는지 여부를 판별하여 논리적 배열 생성
isTargetSpeed = arrayfun(@(x) x.Speed == targetSpeed, simulationResults);

% 논리적 인덱싱을 사용하여 해당 속도의 결과만 필터링
filteredResults = simulationResults(isTargetSpeed);

% 필터링된 결과 출력
disp(filteredResults);



% 필터링 조건: ACLossHighFrequencyScaling_Method, HairpinACLossLocationMethod, HybridACLossMethod 모두 1
filteredResults = simulationResults(arrayfun(@(x) ...
    x.ACLossHighFrequencyScaling_Method == 1 && ...
    x.HairpinACLossLocationMethod ==  1&& ...
    x.HybridACLossMethod == 1, ...
    simulationResults));


% filteredResults 구조체 배열에서 PacTotal 값 추출
Speed                = arrayfun(@(x) x.Speed, filteredResults);
PacByMcadTotalValues = arrayfun(@(x) x.CalcedhybridACLoss.byMcad.PacTotal, filteredResults);
PacCalcTotalValues   = arrayfun(@(x) x.CalcedhybridACLoss.calc.PacTotal, filteredResults);

% save("KDHPC2024WorkSpace4ACLossCompMCAD.mat","PacCalcTotalValues","PacByMcadTotalValues","Speed","simulationResults","hybridACLossPerRPM","PacByMcadTotalValuesScale","PacCalcTotalValuesScale")

% Plot

% PacTotal 값에 대한 그래프 그리기
plot(Speed,PacByMcadTotalValues);
xlabel('Index'); % 인덱스 또는 다른 적절한 라벨
ylabel('PacTotal'); % 적절한 단위를 포함한 라벨
title('PacTotal Values from filteredResults');
grid on;

figure(2)
plot(Speed,PacCalcTotalValues);
xlabel('Index');             % 인덱스 또는 다른 적절한 라벨
ylabel('PacCalcTotal');      % 적절한 단위를 포함한 라벨
title('PacTotal Values from filteredResults');
grid on;

%% 
% 비율 비교
%% 
% * 속도 4배씩 (제곱비) 확인
% * 

% 속도별 차이
index=1
divRatio=[]
for i=length(PacCalcTotalValues):-1:2
divRatio(index)=PacCalcTotalValues(i)./PacCalcTotalValues(i-1)
index=index+1
end

%% Calc와 MCAD차이 비율
RatioCalc4Model.Model1.value=PacByMcadTotalValues/1000./PacCalcTotalValues
RatioCalc4Model.Model2.value=PacByMcadTotalValuesScale/1000./PacCalcTotalValuesScale
RatioCalc4Model.Model3.value=PacByMcadTotalValuesScale/1000./PacCalcTotalValuesScale

[~,RatioCalc4Model.Model1.Path]=mcad(1).GetVariable("CurrentMotFilePath_MotorLAB")
[~,RatioCalc4Model.Model2.Path]=mcad(2).GetVariable("CurrentMotFilePath_MotorLAB")
[~,RatioCalc4Model.Model3.Path]=mcad(3).GetVariable("CurrentMotFilePath_MotorLAB")