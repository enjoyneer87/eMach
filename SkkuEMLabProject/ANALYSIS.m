function ANALYSIS(refPath, refMotFilePath, numPorts, numCases, DoETable, Pole, Slot)
% 상위 경로
parts = strsplit(refPath, filesep);
parentPath = fullfile(parts{1:end-1});

% 병렬풀 초기화 및 배치
delete(gcp('nocreate'));
parpool('Processes', numPorts); % 병렬 풀 생성

% spmd loop, numPorts 병렬 실행
spmd
    spmdIndex
    spmdServers(spmdIndex)=actxserver('motorcad.appautomation');
    % mcad=activeServers(spmdIndex);
    invoke(spmdServers(spmdIndex), 'SetVariable', 'MessageDisplayState', 2); % 모든 메시지를 별도의 창에 표시하도록 설정 - 주의: 이로 인해 파일 저장, 데이터 덮어쓰기 등 중요한 팝업 메시지가 비활성화될 수 있으니 주의하시기 바랍니다.
    invoke(spmdServers(spmdIndex), 'LoadFromFile', refMotFilePath);

    for i = 1:floor(numCases/numPorts)
        caseNum = (spmdIndex-1) * floor(numCases/numPorts) + i;

        spmdServers(spmdIndex).SetVariable('GeometryParameterisation', 1);   % Ratio mode in Motor-CAD

        %% 변수 설정
        % StatorVariable Struct
        StatorVariable=McadStatorVariable([]);
        StatorVariable.Slot_Number=Slot;  % 외부에서 당겨옴
        StatorVariable.Stator_Lam_Dia=220;  % 상수, 고정
        StatorVariable.Tooth_Tip_Depth=0.2;  % 상수, 고정
        StatorVariable.Tooth_Tip_Angle=DoETable.Tooth_Tip_Angle(numCases);  % 상수
        StatorVariable.Stator_Bore=DoETable.Ratio_Bore(numCases);  % 비율
        StatorVariable.Slot_Depth=DoETable.Ratio_SlotDepth_ParallelSlot(numCases);  % 비율
        temp_StatorBore=StatorVariable.Stator_Lam_Dia*StatorVariable.Stator_Bore;  % 계산용
        temp_BackYoke=(StatorVariable.Stator_Lam_Dia-temp_StatorBore)/2*(1-StatorVariable.Slot_Depth);  % 계산용
        temp_Slot_Width_max=temp_BackYoke/DoETable.i_YtoT(numCases);  % 계산용
        StatorVariable.Slot_Width=(temp_StatorBore*pi/StatorVariable.Slot_Number)/temp_Slot_Width_max;  % 비율
        StatorVariable.Slot_Opening=DoETable.Slot_Opening(numCases);  % 비율
        StatorVariable.Sleeve_Thickness=0;  % 비율, 고정
%         i_YtoT=3;
%         statorvariable.Ratio_SlotWidth                   =   []; %% Passive
%         statorDepth=calcBackIronThickness(220,statorvariable.Ratio_Bore,statorvariable.Ratio_SlotDepth_ParallelSlot,0.5);
%         p_Stator_Slots=48;
%         [Rint, slot_pitch, MidToothWidth, Angle_Radian_ToothWidth, Ratio_SlotWidth] = calcImplicitSlotWidthRatio(statorDepth, i_YtoT, p_Tooth_Tip_Depth, i_Stator_OD, i_Split_Ratio, p_Stator_Slots);
%         statorvariable.Ratio_SlotWidth = Ratio_SlotWidth;
        setMcadVariable(StatorVariable,spmdServers(spmdIndex));

        % RotorVariable Struct
        RotorVariable=motorCadGeometryRotor(DoETable(caseNum,:));
        setMcadVariable(RotorVariable(caseNum,:),spmdServers(spmdIndex));

        % EtcVariable Struct
        EtcVariable=struct();
        EtcVariable.Rotor_Lam_Length           =    DoETable.setting_ActiveLength(numCases);
        EtcVariable.Stator_Lam_Length          =    DoETable.setting_ActiveLength(numCases);
        EtcVariable.Magnet_Length              =    DoETable.setting_ActiveLength(numCases);
        EtcVariable.Motor_Length               =    DoETable.setting_ActiveLength(numCases)+100;
        EtcVariable.Shaft_Dia=75;
        EtcVariable.Shaft_Dia_Front=75;
        EtcVariable.Shaft_Dia_Rear=75;
        setMcadVariable(EtcVariable,spmdServers(spmdIndex));
   
        % Winding
        settedConductorData.FillFactor = 60;
        settedConductorData.Turn = 10;
        settedConductorData.parallelTurn = 2;
        settedConductorData.ins_Thick = 0.1; % 도체 절연체 두께
        settedConductorData.Liner_Thick = 0.25; % 절연지 두께
        settedConductorData.Copper_Depth = 100; % 슬롯 몇적의 몇%가 conductor로 채워지는지
        settedConductorData.Conductor_Separation = 0.18; % 도체사이 거리
        validGeometry=spmdServers(spmdIndex).CheckIfGeometryIsValid(1);  % Motor-CAD 자체 기능
        if validGeometry==1
            spmdServers(spmdIndex).SetVariable('MessageDisplayState', 2);
            newFolder = fullfile(parentPath, 'DOE', ['Design', sprintf('%03d', caseNum)]);
            parts = strsplit(newFolder, filesep);
            newMotFilePath = fullfile(newFolder, strcat(parts{end}, '.mot'));

            [Success,settedConductorData.Area_slot]=  spmdServers(spmdIndex).GetVariable('Area_Slot');
            [Success,settedConductorData.slot_width]= spmdServers(spmdIndex).GetVariable('Slot_Width');  % 슬롯 가로길이
            [Success,settedConductorData.slot_depth]= spmdServers(spmdIndex).GetVariable('Slot_Depth');
            NewConductorData=calcConductorSize(settedConductorData);  % 현재 셋팅된 값 기반으로 copper 사이즈 계산
            spmdServers(spmdIndex).SetVariable('Copper_Width',NewConductorData.effective_slot_width);
            spmdServers(spmdIndex).SetVariable('Copper_Height',NewConductorData.effective_slot_Depth);

            spmdServers(spmdIndex).SaveToFile(newMotFilePath);  % winding 설정 반영이 잘 안되서 한번 더 저장
        end

        %% Check, Save, Run
        % Geometry Check
        spmdServers(spmdIndex).CheckIfGeometryIsValid(1);

        % temporal Output
        spmdServers(spmdIndex).DoWeightCalculation();
        [Success,o_Weight_Stat_Core]=spmdServers(spmdIndex).GetVariable('Weight_Total_Stator_Lam');

        % 새 폴더 새 파일
        newFolder = fullfile(parentPath, 'DOE', ['Design', sprintf('%03d', caseNum)]);
        parts = strsplit(newFolder, filesep);
        newMotFilePath = fullfile(newFolder, strcat(parts{end}, '.mot'));
        if ~exist(newFolder, 'dir')
            mkdir(newFolder);
        end
        if ~exist(newMotFilePath, 'file')
            spmdServers(spmdIndex).SaveToFile(newMotFilePath);
        end

        % 
        FileParameters_MotorLAB=struct();
        FileParameters_MotorLAB.CurrentMotFilePath_MotorLAB=[];
        FileParameters_MotorLABFieldsName=fieldnames(FileParameters_MotorLAB);
        [Success,charTypeData]=spmdServers(spmdIndex).GetVariable(FileParameters_MotorLABFieldsName{1});
        FileParameters_MotorLAB.(FileParameters_MotorLABFieldsName{1})=charTypeData;

        % 현재 mot 파일과 refMotFilePath 비교
        if ~isequal(refMotFilePath, FileParameters_MotorLAB.CurrentMotFilePath_MotorLAB)
            [Success, isBuildSucceeded]=spmdServers(spmdIndex).GetModelBuilt_Lab();  % 모델 빌드 여부 체크

            if isBuildSucceeded==0      % 빌드 안되있으면
                spmdServers(spmdIndex).BuildModel_Lab();  % 빌드(해석 실행 및 자동 저장)
                
                % Radial, Axial, Winding Screenshoot 저장
                screens = {'Radial','StatorWinding'};
                for j = 1:numel(screens)
                    screenname = screens{j};
                    fileName = [newFolder, '_Pic_', screenname, '.png'];
                    spmdServers(spmdIndex).SaveScreenToFile(screenname, fileName);
                end

                spmdServers(spmdIndex).LoadFromFile(refMotFilePath);  % ref 파일 땡겨오기
            end
        end
    end  % for 문 끝

    % 종료
    invoke(spmdServers(spmdIndex), 'Quit');
    spmdServers=0;
end

%% 병렬 풀
delete(gcp);

end