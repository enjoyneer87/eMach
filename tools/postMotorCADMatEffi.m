function postMotorCADMatEffi(Speed, Shaft_Torque, Efficiency, Shaft_Power, DC_Bus_Voltage)
%% 산점도의 효율 데이터를 토크와 속도의 규칙적인 격자에 매핑합니다.
% 속도와 토크 범위 추출
vMin = min(min(Speed)); % 최소 속도 추출
vMax = max(max(Speed)); % 최대 속도 추출
tMin = min(min(Shaft_Torque)); % 최소 토크 추출
tMax = max(max(Shaft_Torque)); % 최대 토크 추출

% torque와 speed 범위에 대한 mesh 생성
vVec = linspace(vMin,vMax,10); % 속도 벡터 생성
tVec = [linspace(tMin,tMin/10,10) linspace(tMax/10,tMax,10)]; % zero 회피

% 토크와 속도 범위에 대한 mesh 생성
[tVecMesh,vVecMesh] = meshgrid(tVec,vVec);

% 'nearest' 옵션을 사용하여 극한 토크 및 속도 값에서 외삽을 허용하려면
% 산점보간을 사용하여 효율을 격자 위에서 규칙적으로 결정합니다.
% 중복 값 경고를 끕니다.
MSGID = 'MATLAB:scatteredInterpolant:DupPtsAvValuesWarnId';
warning('OFF', MSGID)
eMat = griddata(Shaft_Torque,Speed,Efficiency,tVecMesh,vVecMesh,'nearest');
warning('ON', MSGID)

%% 최대 출력 값을 추출합니다.
% 모터 및 드라이브 (시스템 레벨) 블록에 사용할 수 있는 최대 출력 값을 추출합니다.
% tMax는 최대 토크 값을 사용할 수 있습니다.
pMax = max(max(Shaft_Power));

%% DC 버스 전압 추출
% Motor-CAD에서 효율을 결정할 때 사용된 DC 버스 전압과 같은 값을
% Simscape 모델에 사용합니다.
vDC = max(max(DC_Bus_Voltage));

% 임시 변수 삭제
clear vMin vMax tMin MSGID tVecMesh vVecMesh DC_Bus_Voltage
end
