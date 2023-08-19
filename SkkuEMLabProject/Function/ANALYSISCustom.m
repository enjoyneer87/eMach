function ANALYSISCustom(refMotFilePath, NumberOfPorts, NumberOfCases, DoETable, FixVariableStruct, message_on)
%


%% 병렬풀 초기화 및 배치
delete(gcp('nocreate'));  % 사전에 실행 중인 병렬 풀 있을까봐 끄고 시작
parpool(NumberOfPorts);  % 병렬 풀 생성, default가 Processes, Threads로 하면 에러
% spmd loop, numPorts 병렬 실행
if message_on>0
    time_before_spmd=datetime;
    disp(['The ', num2str(NumberOfPorts), ' ports ', num2str(NumberOfCases), ' cases spmd start'])
    disp(['Time at spmd start : ', char(time_before_spmd)])
end


spmd
    mcad(spmdIndex)=actxserver('motorcad.appautomation');

    invoke(mcad(spmdIndex), 'SetVariable', 'MessageDisplayState', 2);  % 모든 메시지를 별도의 창에 표시하도록 설정 - 주의: 이로 인해 파일 저장, 데이터 덮어쓰기 등 중요한 팝업 메시지가 비활성화될 수 있으니 주의하시기 바랍니다.
    invoke(mcad(spmdIndex), 'LoadFromFile', refMotFilePath);
    mcad(spmdIndex).InitialiseTabNames()

    for OrderInPort = 1:1:(NumberOfCases/NumberOfPorts)
        
        CaseNumber = (spmdIndex-1)*(NumberOfCases/NumberOfPorts)+OrderInPort;  % parallel case number seperation
        if message_on>1
            disp(['case ',num2str(CaseNumber),' start'])
            disp(['Time at case start : ', char(datetime)])
        end
        mcad(spmdIndex).SetVariable('MessageDisplayState', 2);

        %% New Folder and File Address
        parts = strsplit(refMotFilePath, filesep);
        % % 코드 있는것 보다 상위 폴더에 DOE 폴더 만들고 저장
        % parentPath = fullfile(parts{1:end-2});  
        % [filepath,name,ext] = fileparts(refMotFilePath);
        % newFolder = fullfile(parentPath, 'DOE', [name, '_Design', sprintf('%03d', CaseNumber)]);
        % 코드 있는 폴더에 DOE 폴더 만들고 저장
        codePath = fullfile(parts{1:end-1});  
        [~,name,~] = fileparts(refMotFilePath);
        newFolder = fullfile(codePath, 'DOE', [name, '_Design', sprintf('%04d', CaseNumber)]);

        parts = strsplit(newFolder, filesep);
        newMotFilePath = fullfile(newFolder, strcat(parts{end}, '.mot'));
        resultcheckfolder=[newFolder '\ResultCheck'];  % 해석 완료된 모델 체크용
        geometrycheckfolder=[newFolder '\GeometryCheck'];

        %% ResultCheck & GeometryCheck 폴더가 없을때만 진행, 있으면 case 넘기기
        if ~exist(resultcheckfolder, 'dir') && ~exist(geometrycheckfolder, 'dir')
            % 저장하고 시작
            mcad(spmdIndex).SaveToFile(newMotFilePath);
            addpath(newFolder);
            if message_on>1
                disp(['case ',num2str(CaseNumber),' new file save'])
            end

            %% StatorVariable Struct
            StatorVariable=McadStatorVariable([]);
            StatorVariable.SlotType=2;  % slot type : parallel slot
            StatorVariable.Slot_Number=FixVariableStruct.Slot_Number;  % 외부에서 당겨옴, 상수, 고정
            StatorVariable.Stator_Lam_Dia=FixVariableStruct.Stator_Lam_Dia;  % 외부에서 당겨옴, 상수, 고정
            StatorVariable.Tooth_Tip_Depth=FixVariableStruct.Tooth_Tip_Depth;  % 외부에서 당겨옴, 상수, 고정
            StatorVariable.Tooth_Tip_Angle=DoETable.Tooth_Tip_Angle(CaseNumber);  % 상수
            % StatorVariable.Stator_Bore=StatorVariable.Stator_Lam_Dia*DoETable.Ratio_Bore(caseNum);  % 상수
            % StatorVariable.Slot_Depth=(StatorVariable.Stator_Lam_Dia-StatorVariable.Stator_Bore)*DoETable.Ratio_SlotDepth_ParallelSlot(caseNum);  % 상수
            % StatorVariable.Slot_Width=(StatorVariable.Stator_Lam_Dia-StatorVariable.Stator_Bore-StatorVariable.Slot_Depth)*DoETable.i_YtoT(caseNum);  % 상수
            % StatorVariable.Slot_Opening=StatorVariable.Slot_Width*DoETable.Ratio_SlotOpening_ParallelSlot(caseNum);  % 상수
            % StatorVariable.Sleeve_Thickness=0;  % 상수
            StatorVariable.Ratio_Bore=DoETable.Ratio_Bore(CaseNumber);  % 비율
            StatorVariable.Ratio_SlotDepth_ParallelSlot=DoETable.Ratio_SlotDepth_ParallelSlot(CaseNumber);  % 비율
            % temp_StatorBore=StatorVariable.Stator_Lam_Dia*StatorVariable.Ratio_Bore;  % 계산용
            % temp_BackYoke=(StatorVariable.Stator_Lam_Dia-temp_StatorBore)/2*(1-StatorVariable.Ratio_SlotDepth_ParallelSlot);  % 계산용
            % temp_Teeth_Width=temp_BackYoke/DoETable.i_YtoT(CaseNumber);  % 계산용
            % temp_SlotWidth=(temp_StatorBore*pi/StatorVariable.Slot_Number)-temp_Teeth_Width;  % 계산용
            % StatorVariable.Ratio_SlotWidth=temp_SlotWidth/(temp_StatorBore*pi/StatorVariable.Slot_Number);  % 비율
            StatorVariable.Ratio_SlotWidth=DoETable.Ratio_SlotWidth;  % 비율
            StatorVariable.Ratio_SlotOpening_ParallelSlot=DoETable.Ratio_SlotOpening_ParallelSlot(CaseNumber);  % 비율
            StatorVariable.Ratio_SleeveThickness=0;  % 비율, 고정

            setMcadVariable(StatorVariable,mcad(spmdIndex));

            %% RotorVariable Struct (그냥 구조체가 아님, 변수 추가하려면 "motorCadGeometryRotor" 내부에서 정의 후 진행)
            RotorVariable=motorCadGeometryRotor(DoETable(CaseNumber,:),FixVariableStruct.VMagnet_Layers);
            RotorVariable.BPMRotor=FixVariableStruct.BPMRotor;
            RotorVariable.PoleNumber_Outer=FixVariableStruct.Pole_Number;
            RotorVariable.VMagnet_Layers=FixVariableStruct.VMagnet_Layers;
            % RotorVariable.Banding_Thickness=FixVariableStruct.Banding_Thickness;  % 고정
            RotorVariable.Ratio_BandingThickness=FixVariableStruct.Ratio_BandingThickness;  % 고정
            % RotorVariable.Shaft_Dia=FixVariableStruct.Shaft_Dia;  % 고정
            temp_Rotor_Dia=StatorVariable.Stator_Lam_Dia*DoETable.Ratio_Bore(CaseNumber)-2*FixVariableStruct.Airgap;
            RotorVariable.Ratio_ShaftD=FixVariableStruct.Shaft_Dia/temp_Rotor_Dia;
            RotorVariable.Shaft_Dia_Front=FixVariableStruct.Shaft_Dia;  % 샤프트 외경 고정
            RotorVariable.Shaft_Dia_Rear=FixVariableStruct.Shaft_Dia;  % 샤프트 외경 고정
            RotorVariable.Airgap=FixVariableStruct.Airgap;  % 고정
            RotorVariable.VShapeMagnetSegments_Array=FixVariableStruct.VShapeMagnetSegments_Array;
            RotorVariable.BridgeThickness_Array=FixVariableStruct.BridgeThickness_Array;

            setMcadVariable(RotorVariable,mcad(spmdIndex));

            %% EtcVariable Struct, Axial parameters...
            EtcVariable=struct();
            % EtcVariable.N_d_MotorLAB=DoETable.N_d_MotorLAB(caseNum);
            % EtcVariable.Imax_MotorLAB=DoETable.Imax_MotorLAB(caseNum);
            EtcVariable.Rotor_Lam_Length           = DoETable.ActiveLength(CaseNumber);
            EtcVariable.Stator_Lam_Length          = DoETable.ActiveLength(CaseNumber);
            EtcVariable.Magnet_Length              = DoETable.ActiveLength(CaseNumber);
            EtcVariable.Motor_Length               = DoETable.ActiveLength(CaseNumber)+100;
            EtcVariable.AxialSegments              = FixVariableStruct.AxialSegments;  % 영구자석 축방향 분할

            setMcadVariable(EtcVariable,mcad(spmdIndex));

            %% Winding
            settedConductorData=struct();
            % NewConductorData=struct();
            settedConductorData.Armature_CoilStyle = FixVariableStruct.Armature_CoilStyle;  % Coil Style : Hairpin
            settedConductorData.Insulation_Thickness = FixVariableStruct.Insulation_Thickness;  % 도체 절연체 두께
            settedConductorData.Liner_Thickness = FixVariableStruct.Liner_Thickness;  % 절연지 두께
            settedConductorData.WindingLayers=FixVariableStruct.WindingLayers;  % 슬롯 내 턴 수
            settedConductorData.ParallelPaths_Hairpin=FixVariableStruct.ParallelPaths_Hairpin;  % 병렬 수
            % settedConductorData.ConductorsPerSlot=FixVariableStruct.ConductorsPerSlot;  % WindingLayers 에 따라 자동으로 적용됨
            settedConductorData.ConductorSeparation = FixVariableStruct.ConductorSeparation;  % 방사방향 도체 사이 거리
            settedConductorData.temp_fillfactor = FixVariableStruct.temp_fillfactor;  % temp
            settedConductorData.HairpinWindingPatternMethod = FixVariableStruct.HairpinWindingPatternMethod;  % Improved
            settedConductorData.MagThrow = FixVariableStruct.MagThrow;  % 권선 피치

            setMcadVariable(settedConductorData,mcad(spmdIndex));
        
            %% Geometry Check 
            validGeometry=mcad(spmdIndex).CheckIfGeometryIsValid(0);  % Motor-CAD 자체 기능, geometry 보완
            if ~validGeometry
                mkdir(geometrycheckfolder);
                addpath(geometrycheckfolder);
                if message_on>0
                    disp(['geometry wrong and GeomertyCheck folder made'])
                end
            end
            
            %% Custom Geometry
            setCustomRotorPoint(mcad(spmdIndex))

            %% Save
            mcad.ShowMechanicalContext()
            mcad.ShowMagneticContext()
            % mcad(spmdIndex).SaveToFile(newMotFilePath);

            %% Hair-pin coil function
            if validGeometry
                [~,settedConductorData.Area_Slot]=mcad(spmdIndex).GetVariable('Area_Slot');  % 슬롯 영역 넓이
                [~,settedConductorData.Area_Winding_With_Liner]=mcad(spmdIndex).GetVariable('Area_Winding_With_Liner');  % 직사각각형 슬롯 영역 넓이
                [~,settedConductorData.Slot_Width]= mcad(spmdIndex).GetVariable('Slot_Width');  % 슬롯 너비 (회전방향)
                [~,settedConductorData.Winding_Depth]=mcad(spmdIndex).GetVariable('Winding_Depth');  % 직사각형 슬롯 깊이 (방사방향)
                % [Success,settedConductorData.Slot_Depth]= activeServers(spmdIndex).GetVariable('Slot_Depth');  % 슬롯 깊이 (방사방향)
                NewConductorData=calcConductorSize(settedConductorData, message_on);  % 현재 셋팅된 값 기반으로 copper 사이즈 계산

                setMcadVariable(NewConductorData,mcad(spmdIndex));
                if message_on>1
                    disp(['case ', num2str(CaseNumber),' setting done'])
                end
                %% Radial, Axial, Winding Screenshoot 저장
                screens = {'Radial','StatorWinding'};
                for j = 1:numel(screens)
                    screenname = screens{j};
                    fileName = [newFolder, '\Pic_', screenname, '.png'];
                    mcad(spmdIndex).SaveScreenToFile(screenname, fileName);
                end
                %% build
                mcad(spmdIndex).SaveToFile(newMotFilePath);  % 빌드 전 저장
                addpath(genpath(newFolder));
                % 현재 파일 vs. ref 파일 다른거 맞는지 체크
                [~,CurrentMotFilePath_MotorLAB]=mcad(spmdIndex).GetVariable('CurrentMotFilePath_MotorLAB');
                if isequal(refMotFilePath, CurrentMotFilePath_MotorLAB)
                    error(['case ',num2str(CaseNumber),' (', num2str(OrderInPort), 'th in port ', num2str(spmdIndex),') does not copied'])
                end

                % build 반복
                time_before=datetime;  % build 전 시간
                if message_on>1
                    disp(['Time before build : ', char(time_before)])
                end
                [~, isBuildSucceeded]=mcad(spmdIndex).GetModelBuilt_Lab();
                while ~isBuildSucceeded
                    mcad(spmdIndex).BuildModel_Lab();
                    [~, isBuildSucceeded]=mcad(spmdIndex).GetModelBuilt_Lab();
                end


                % 파일 저장, build 완료 체크용 폴더 생성
                [~, isBuildSucceeded]=mcad(spmdIndex).GetModelBuilt_Lab();
                if isBuildSucceeded
                    mcad(spmdIndex).SaveToFile(newMotFilePath);  % 파일 재저장
                    addpath(genpath(newFolder));                   
                    mkdir(resultcheckfolder);  % 빌드 완료됨을 표시하는 폴더 생성
                    addpath(resultcheckfolder);
                    time_after=datetime;  % build 후 시간
                    if message_on>0
                        disp(['case ',num2str(CaseNumber),' (', num2str(OrderInPort), 'th in port ', num2str(spmdIndex),') build done'])
                        disp(['Time after build : ', char(time_after)])
                        disp(['Time cost of build : ', char(time_after-time_before)])
                    end
                else
                    error(['case ',num2str(CaseNumber),' (', num2str(OrderInPort), 'th in port ', num2str(spmdIndex),') does not build'])
                end

                % ref 파일 땡겨오기
                mcad(spmdIndex).LoadFromFile(refMotFilePath);
            end

        else  % ResultCheck 또는 GeometryCheck 폴더가 있을 때
            if message_on>0 && exist(resultcheckfolder, 'dir') && ~exist(geometrycheckfolder, 'dir')
                disp(['case ', num2str(CaseNumber), ' is already done, move to next case'])
            elseif message_on>0 && ~exist(resultcheckfolder, 'dir') && exist(geometrycheckfolder, 'dir')
                disp(['case ', num2str(CaseNumber), ' is geometry wrong, move to next case'])
            else
                disp(['case ', num2str(CaseNumber), ' is unclassified error, move to next case'])
            end
        end

        if message_on>1
            disp(['case ',num2str(CaseNumber),' end'])
            disp(['Time at case end : ', char(datetime)])
        end
    end  % spmdIndex 별 for 문 끝

    %% spmdIndex 종료
    invoke(mcad(spmdIndex), 'Quit');
    mcad=0;
    if message_on>0
        disp(['port ', num2str(spmdIndex), ' loop end'])
    end

end  % spmd end

%% 전체 알고리즘 종료
delete(gcp);
if message_on>0
    time_after_spmd=datetime;
    disp(['The ', num2str(NumberOfPorts), ' ports ', num2str(NumberOfCases), ' cases spmd end'])
    disp(['Time at spmd end : ', char(time_after_spmd)])
    disp(['Time cost of spmd : ', char(time_after_spmd-time_before_spmd)])
end

end  % function end