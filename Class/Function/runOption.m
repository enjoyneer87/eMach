%% MotorCAD 전체 입력변수 객체 사전 생성 필요여부



%% 
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


%% Calibration 객체로 넘기기
HDEVBemfCalibration.refValues.StatorSaturationMultiplier   =HDEV1motorcad.multiplier.StatorSaturationMultiplier   ;
HDEVBemfCalibration.refValues.RotorSaturationMultiplier    =HDEV1motorcad.multiplier.RotorSaturationMultiplier    ;
HDEVBemfCalibration.refValues.MagneticAxialLengthMultiplier=HDEV1motorcad.multiplier.MagneticAxialLengthMultiplier;

%% 최적화 실행
% calibration.multiplier 구조체에서 모든 double 변수값을 추출하여 벡터로 저장
refValues = cell2mat(struct2cell(HDEVBemfCalibration.refValues));

% 모든 값에 105%를 곱하여 상한 값(max)과 하한 값(min)을 정의
mc_input_max = 1.05 * refValues;
mc_input_min = 0.95 * refValues;

% 최적화 옵션 정의
options = optimoptions('fmincon', 'Display', 'iter', 'Algorithm', 'interior-point');
% 최적화 함수 정의
objfun = @(x) norm(abs(fft(signal_csv)) - abs(fft(HDEV1motorcad.calibrationMotorcadAnalysis(x))))^2;
% 최적화 실행
mc_input_optimized = fmincon(objfun, 0, [], [], [], [], mc_input_min, mc_input_max, [], options);


