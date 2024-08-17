function ComponentTable=mkConductorSingleSeries(PhaseParaName,,app,PositionY)
%% dev
% PhaseParaName='U1'
% CoilList=[1,5,13,19]
if nargin<4
    PositionY=43;
end
%% 각 변수의 초기값 설정
ComponentName = {};  % 셀 배열로 초기화
position = {};       % 숫자 배열로 초기화
ComponentObj = {};   % 셀 배열로 초기화
InstanceObj = {};    % 셀 배열로 초기화

% 테이블 생성
ComponentTable = table(ComponentName, position, ComponentObj, InstanceObj, ...
    'VariableNames', {'ComponentName', 'position', 'aComponent', 'aInstance'});

%%

ComponentName
position{ComponentIndex}                    =[ComponentIndex*4-10,PositionY];
[aComponent,aInstance]                      =mkConductorComp(ComponentName{ComponentIndex},app,position{ComponentIndex} );
ComponentTable.ComponentName(ComponentIndex)=ComponentName(ComponentIndex);
ComponentTable.position{ComponentIndex}     =position{ComponentIndex}     ; 
ComponentTable.aComponent{ComponentIndex}   =aComponent   ;     
ComponentTable.aInstance{ComponentIndex}    =aInstance    ;     
end
