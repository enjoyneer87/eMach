
% 1 Declare MotorCADData object
% 2 Calibrable Coefficient for BEMF
% 3 Phase EMF Import 
% EMF Simulation Import & test value
% Coherence sampling &  3고조파 제거 코드
% 4. PostProcessor
% 5. Calibration (%% 5.  주파수 영역 비교)

%% 1 Declare MotorCADData object

HDEV1motorcad=MotorcadData(12);
HDEV1motorcad.motorcadMotPath='Z:\Thesis\Optislang_Motorcad\Validation'
HDEV1motorcad.motorcadMotPath='Z:\Thesis\Optislang_Motorcad\Validation'
HDEV1motorcad.proj_path=HDEV1motorcad.motorcadMotPath;
HDEV1motorcad.file_path=HDEV1motorcad.proj_path;
HDEV1motorcad.file_name='HDEVModel1BEMF'

% Input 정의 
% basic drive &circuit data
HDEV1motorcad.Rs= 0.0067;   
HDEV1motorcad.Vdc=650;
HDEV1motorcad.Vs_max=HDEV1motorcad.Vdc*(2/pi)*0.98 % dankai
HDEV1motorcad.Is_max=750;     %pk value

% manufacturingInfo

% HDEV1motorcad.manufacturingInfo.NumberStatorLamination  
% HDEV1motorcad.manufacturingInfo.NumberRotorLamination   
% Solver
MagneticSolver = 0;


% Calc Method
StackingFactor_Magnetics                  = 2    ;                  
StackingFactorIronLossMethod              = 1    ;          
ProximityLossModel                        = 1    ; 
HybridACLossMethod                        = 1    ; 
LabModel_ACLoss_Method                    = 1    ;     

%  Miscellaneous Method


%% 2 Calibrable Coefficient for BEMF
% 1. Br
% 2. alpha
% 3. Hc
% 4. beta

% Stacklength Coefficient
% 8. stator Factor
% 9. Rotor Factor
HDEV1motorcad.multiplier.StatorSaturationMultiplier         =0.97;     % 7. Saturation Factor?
HDEV1motorcad.multiplier.RotorSaturationMultiplier          =0.97;     %
HDEV1motorcad.multiplier.MagneticAxialLengthMultiplier      =0.98;     %

% Multiplier
% Manufacturing Factors:
HDEV1motorcad.multiplier.ArmatureEWdgMLT_Multiplier                               =1;
HDEV1motorcad.multiplier.ArmatureEWdglnductance_Multiplier                        =1;
HDEV1motorcad.multiplier.Magnet_Br_Multiplier                                     =0.95;    % 5. Br coefficient
HDEV1motorcad.multiplier.ArmatureEWdgMLT_Aux_Multiplier                           =1;
HDEV1motorcad.multiplier.ArmatureEWdglnductance_Aux_Multiplier                    =0.97;

% Length Adjustment Factors
HDEV1motorcad.multiplier.StatorSaturationMultiplier                               =0.95;     % 7. Saturation Factor?
HDEV1motorcad.multiplier.RotorSaturationMultiplier                                =0.95;
HDEV1motorcad.multiplier.MagneticAxialLengthMultiplier                            =1;

% etc
HDEV1motorcad.multiplier.StatorLeakagelnductance_Aux_Multiplier                   =1;
HDEV1motorcad.multiplier.Magnetizinglnductance_Aux_Multiplier                     =1;
HDEV1motorcad.multiplier.RotorLeakagelnductance_Multiplier                        =1;
HDEV1motorcad.multiplier.StatorlronLossBuildFactor                                =1;
HDEV1motorcad.multiplier.ShaftLossBuildFactor                                     =1;
HDEV1motorcad.multiplier.FieldEWdgMLT_Multiplier                                  =1;
HDEV1motorcad.multiplier.HysteresisLossBuildFactor                                =1;
HDEV1motorcad.multiplier.EddyLossBuildFactor                                      =1;
HDEV1motorcad.multiplier.FluxLinkageMultiplier_Q                                  =1;
HDEV1motorcad.multiplier.FluxLinkageMultiplier_D                                  =1;
HDEV1motorcad.multiplier.IMEquivCircMultipliersDefinition                         =1;
HDEV1motorcad.multiplier.Proximity_Winding_Resistance_Multiplier                  =1;

% 6. Hc coefficient
HDEV1motorcad.multiplier.RotorlronLossBuildFactor                                 =1.5;
HDEV1motorcad.multiplier.MagnetLossBuildFactor                                    =1.5;
HDEV1motorcad.multiplier.StatorLeakagelnductance_Multiplier                       =1;
HDEV1motorcad.multiplier.SleeveAxialLengthMultiplier                              =1;
HDEV1motorcad.multiplier.Magnetizinglnductance_Multiplier                         =1;


%% 3 Phase EMF Import 
% 2)Import csv or .dat or From Measured Data
file_path='Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\EMF\오실로 역기전력 데이터\'
file_name='C1--test_EMF_1000rrpm--00001.csv';
MeasuredEMF=csv_to_table(file_path,file_name);
onePeriodMeasuredEMF=One_period_sampling(MeasuredEMF,1000,12);

%% EMF Simulation Import & test value
% from (test) Simulation data
% MotorCADEMFph=readmatrix('Z:\01_Codes_Projects\Testdata_post\BEMF_motorcad.csv');
% MotorCADEMFph=BEMFsample.y
% MotorCADEMFph1=MotorCADEMFph([2:end],2);
B_emf_ph1=readmatrix('Z:\01_Codes_Projects\Testdata_post\BEMF_motorcad.csv')
MotorCADEMFph1=B_emf_ph1(2:end-1,2)'
% MotorCADEMFph1=MotorCADEMFph(3:end)
% from Simulation data
% 변수 입력

%

%% Coherence sampling &  3고조파 제거 코드

[coMotorCADEMFph1,coMeasuredEMF]=coherenceSampling(MotorCADEMFph1,onePeriodMeasuredEMF);
coMotorCADEMFph1=coMotorCADEMFph1'
plot([coMotorCADEMFph1,coMeasuredEMF]);
hold on
figureCenter;
a=fft(coMotorCADEMFph1)
coMotorCADEMFph1wo3rdH =zeroOut3ncoeffs(coMotorCADEMFph1);

realcoMotorCADEMFph1wo3rdH=real(coMotorCADEMFph1wo3rdH)
modifiedStep=12
plot(coMeasuredEMF)
hold on
plot([realcoMotorCADEMFph1wo3rdH(modifiedStep:end)' realcoMotorCADEMFph1wo3rdH(1:modifiedStep-1)'])
%% 4. PostProcessor



%% 5. Calibration (%% 5.  주파수 영역 비교)

HDEVBemfCalibration=CalibrationMotorCAD("HDEVBEMF1000rpm",'BackEMFPh1',onePeriodMeasuredEMF,HDEV1motorcad.multiplier,HDEV1motorcad.multiplier)

% Calibration 객체로 넘기기
HDEVBemfCalibration.refVar.StatorSaturationMultiplier   =HDEV1motorcad.multiplier.StatorSaturationMultiplier   ;
HDEVBemfCalibration.refVar.RotorSaturationMultiplier    =HDEV1motorcad.multiplier.RotorSaturationMultiplier    ;
HDEVBemfCalibration.refVar.MagneticAxialLengthMultiplier=HDEV1motorcad.multiplier.MagneticAxialLengthMultiplier;

% calibration.multiplier 구조체에서 모든 double 변수값을 추출하여 벡터로 저장
refValues = cell2mat(struct2cell(HDEVBemfCalibration.refVar));

% 모든 값에 105%를 곱하여 상한 값(max)과 하한 값(min)을 정의
mc_input_max = 1.05 * refValues;
mc_input_min = 0.95 * refValues;
 
% define ResultMotorcadEmagData object
% c2Transient=ResultMotorcadEmagData(HDEV1motorcad) % define object


BEMFsample=exportMotorcadResult(HDEVBemfCalibration); % have internally extractGraphMotorCad fcn



%% Shift Wave 


% %% 
% t2 = Eangle; % 두번째 그래프의 시간 범위
% x2 = C2; % 두번째 그래프
% % 그래프 길이를 맞추기 위해 resample 함수 사용
% 
% %% ReSampling
% new_t = Eangle; % 새로운 시간 범위
% new_x1 = interp1(t1, C2,t2); % 첫번째 그래프 재샘플링


