%% 3 Case Study
% % 1 ac loss  포함  Transient
% HDEV1motorcad=motorcadResultExport(HDEV1motorcad)
% % HDEV1motorcad=motorcadCalcandExport(HDEV1motorcad)
% 
% ResultHDEV1motorcad=ResultMotorcadEmagData(HDEV1motorcad) % define object
% setGraphName=acceptVariableNumInputs('BackEMFLineToLine12','BackEMFLineToLine12_1','BackEMFLineToLine12_2'); % define setGraphName should be cell array format 
% c1Transient=c1Transient.exportPlotGraph(setGraphName);
% c1Transient=ResultHDEV1motorcad;
% save('c1Transient.mat', 'c1Transient'); % 객체를 mat 파일로 저장
% 2  미포함   Transient
MagneticSolver = 0
% factor
StackingFactor_Magnetics =1 % 0, 1, 2
% Loss Model
ProximityLossModel = 1;
% etc ;
TransientEmbeddingSolver  =0 ;
FEAEddyCurrentCalcMethod  =1;
HybridACLossMethod =0;
LabModel_ACLoss_Method =1;

c2Transeintmotorcad=HDEV1motorcad;
c2Transeintmotorcad.MagneticSolver=MagneticSolver;
c2Transeintmotorcad.ProximityLossModel=ProximityLossModel;
c2Transeintmotorcad=motorcadResultExport(c2Transeintmotorcad);

c2Transient=ResultMotorcadEmagData(c2Transeintmotorcad) % define object

c2Transient=ResultMotorcadEmagData(HDEV1motorcad) % define object

setGraphName=acceptVariableNumInputs('BackEMFLineToLine12','BackEMFLineToLine12_1','BackEMFLineToLine12_2'); % define setGraphName should be cell array format 
c2Transient=c2Transient.exportPlotGraph(setGraphName);
save('c2Transient.mat', 'c2Transient'); % 객체를 mat 파일로 저장

% 3 포함 Multi-Static
% MagneticSolver = 1
% % factor
% StackingFactor_Magnetics =1 % 0, 1, 2
% % Loss Model
% ProximityLossModel = 2;
% % etc ;
% TransientEmbeddingSolver  =0 ;
% FEAEddyCurrentCalcMethod  =1;
% HybridACLossMethod =0;
% LabModel_ACLoss_Method =1;
% 
% c3Transeintmotorcad=HDEV1motorcad;
% c3Transeintmotorcad.MagneticSolver=MagneticSolver;
% c3Transeintmotorcad.ProximityLossModel=ProximityLossModel;
% c3Transeintmotorcad=motorcadResultExport(c3Transeintmotorcad);
% 
% c3Transient=ResultMotorcadEmagData(c3Transeintmotorcad) % define object
% setGraphName=acceptVariableNumInputs('BackEMFLineToLine12','BackEMFLineToLine12_1','BackEMFLineToLine12_2'); % define setGraphName should be cell array format 
% c3Transient=c3Transient.exportPlotGraph(setGraphName);
% save('c3Transient.mat', 'c3Transient'); % 객체를 mat 파일로 저장


MagneticSolver = 1
% % factor
% StackingFactor_Magnetics =1 % 0, 1, 2
% % Loss Model
% ProximityLossModel = 1;
% % etc ;
% TransientEmbeddingSolver  =0 ;
% FEAEddyCurrentCalcMethod  =1;
% HybridACLossMethod =0;
% LabModel_ACLoss_Method =1;
% 
c4Transeintmotorcad=HDEV1motorcad;
c4Transeintmotorcad.MagneticSolver=MagneticSolver;
c4Transeintmotorcad.ProximityLossModel=ProximityLossModel;
c4Transeintmotorcad=motorcadResultExport(c4Transeintmotorcad);

% save('c4Transient.mat', 'c4Transient'); % 객체를 mat 파일로 저장
% 
% %% 5. 미포함  Reduced Multi-Static
% MagneticSolver = 2
% % factor
% StackingFactor_Magnetics =1 % 0, 1, 2
% % Loss Model
% ProximityLossModel = 1;
% % etc ;
% TransientEmbeddingSolver  =0 ;
% FEAEddyCurrentCalcMethod  =1;
% HybridACLossMethod =0;
% LabModel_ACLoss_Method =1;
% 
% c5Transeintmotorcad=HDEV1motorcad;
% c5Transeintmotorcad.MagneticSolver=MagneticSolver;
% c5Transeintmotorcad.ProximityLossModel=ProximityLossModel;
% c5Transeintmotorcad=motorcadResultExport(c5Transeintmotorcad);
% 
% 
% c5Transient=ResultMotorcadEmagData(c5Transeintmotorcad) % define object
% setGraphName=acceptVariableNumInputs('BackEMFLineToLine12','BackEMFLineToLine12_1','BackEMFLineToLine12_2'); % define setGraphName should be cell array format 
% c5Transient=c5Transient.exportPlotGraph(setGraphName);
% save('c5Transient.mat', 'c5Transient'); % 객체를 mat 파일로 저장
% 
% 
%% 4. Phase EMF Analysis
%  1) Import csv From MotorCAD 
c4Transeintmotorcad=HDEV1motorcad;
c4Transeintmotorcad.MagneticSolver=0;
c4Transeintmotorcad.ProximityLossModel=ProximityLossModel;
mcad = actxserver('MotorCAD.AppAutomation');
mcad.SetVariable('MagneticSolver',c4Transeintmotorcad.MagneticSolver)

% 결과 객체 만들기
c4Transient=ResultMotorcadEmagData(c4Transeintmotorcad) % define Result object

% 해석 
c4Transient=motorcadResultExport(c4Transient) 

% graph 추출을 위한 추출 원하는 그래프 이름 입력
setGraphName=acceptVariableNumInputs('BackEMFPh1','BackEMFPh1_1','BackEMFPh1_2'); % define setGraphName should be cell array format 

% plot graph
c4Transient=c4Transient.exportPlotGraph(setGraphName);


% Define shortEangle - MotorCAD angle
N=length(c4Transient.xgraphDataS.valueforGraph{1});
shortEangle=[0:360/(N-1):360];
f=[0:360/(length(shortEangle)-1):360];
t1 = f; % 첫번째 그래프의 시간 범위
length(shortEangle)


MeasuredEMF
% plot graph
c4Transient=c4Transient.exportPlotGraph(setGraphName);

%% 4. PostProcessor



c4Transientwo3rdH =zeroOut3ncoeffs(c4Transient.xgraphDataS.valueforGraph{1})
plot(shortEangle(1:121),real(c4Transientwo3rdH))
% B_emf_ph_3f = delete3rdHarmonic(MotorCADEMFph1(2:end));
% plot(shortEangle(2:122),MotorCADEMFph1(2:end))
% hold on
% MotorCADEMFph1wo3rdH = zeroOut3ncoeffs(MotorCADEMFph1(2:end));


%% matlab 최적화 fmicon code backup (ing)
% define objfun with fcn exportMotorcadResult and 
calibrationObj=HDEVBemfCalibration
% function y = objfun(x)
%     global calibrationObj
%     if ~isequal(x,xLast) % Check if computation is necessary
%         calibrationObj
%         BEMFsample = exportMotorcadResult(calibrationObj);
%         
%         [myf,myc,myceq] 
% 
%         xLast = x;
%     end
%     % Now compute objective function
%     y = myf + 20*(x(3) - x(4)^2)^2 + 5*(1 - x(4))^2;
% end

Calibration_Main



% 최적화 옵션 정의
options = optimoptions('fmincon', 'Display', 'iter', 'Algorithm', 'interior-point');
% 최적화 함수 정의
% objfun = @(x) norm(signal_csv - calibrationMotorcadAnalysis(x))^2;
% objfun = @(x) norm(signal_csv - HDEVBemfCalibration.run(x))^2;



% 최적화 실행
fun = @objfun; % The objective function, nested below


mc_input_optimized = fmincon(fun, 0, [], [], [], [], mc_input_min, mc_input_max, [], options);
HDEV1motorcad.calibration=HDEVBemfCalibration;
