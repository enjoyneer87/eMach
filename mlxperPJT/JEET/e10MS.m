% Coil모델
% 무부하 파형, 토크, 전류위상각 산출
app=callJmag
app.Show
jprojPath="Z:\Simulation\JEETACLossValid_e10_v24\refModel\e10_v24.jproj";
app.Load(jprojPath)
% 자속파형, 추출
% 인덕턴스 및 파라미터 추출
% calcACLossModel plot

%% skin Depth Model
delta=calcSkinDepth(omega2freq(rpm2OmegaE(1000,4))) % 2.25594 -;
