% function devSetVariableFromTable(DoETable(OrderInPort,:))

    %% Input
    NumberOfPorts = 6;  % 병렬 포트 수
    NumberOfCases = 1000;  % 해석 케이스 수
    
    % 경로 
    refPath='Z:\Simulation\LabProj2023v1\12p72s_VV_HWY\MCAD';  % Motor-CAD 파일 있는 경로
    refFileName='12p72s_VV';  % 해석 파일 이름
    
    % refPath='Z:\01_Codes_Projects\git_fork_emach\SkkuEMLabProject\LabProj2023v1\12p72s_Delta_YMKim\MCAD'
    % refFileName='12P72S_Deltatype';  % 해석 파일 이름
    refMotFileName=strcat(refFileName,'.mot');
    refMotFilePath = fullfile(refPath,refMotFileName);
    
    % Doe Table
    DoeTablePath=fullfile(refPath,"DoeTable.mat");
    load(DoeTablePath);
    
    message_on=0;
    mcad.AvoidImmediateUpdate(true)
    mcad.SetVariable("MessageDisplayState",2)
    mcad.SetVisible(1)

%% After testCode


    %% Set Variable   
    % for CaseNumber=1:height(DoETable)
    tic
    for CaseNumber=1:10
            % StatorVariable Struct
        StatorVariable                                  =McadStatorVariable([]);
        StatorVariable.SlotType                         =2;  % slot type : parallel slot
        StatorVariable.Slot_Number                      =FixVariableTable.Slot_Number;  % 외부에서 당겨옴, 상수, 고정
        StatorVariable.Stator_Lam_Dia                   =FixVariableTable.Stator_Lam_Dia;  % 외부에서 당겨옴, 상수, 고정
        StatorVariable.Tooth_Tip_Depth                  =FixVariableTable.Tooth_Tip_Depth;  % 외부에서 당겨옴, 상수, 고정
        StatorVariable.Tooth_Tip_Angle                  =DoETable.Tooth_Tip_Angle(CaseNumber);  % 상수
        % StatorVariable.Stator_Bore=StatorVariable.Stator_Lam_Dia*DoETable.Ratio_Bore(caseNum);  % 상수
        % StatorVariable.Slot_Depth=(StatorVariable.Stator_Lam_Dia-StatorVariable.Stator_Bore)*DoETable.Ratio_SlotDepth_ParallelSlot(caseNum);  % 상수
        % StatorVariable.Slot_Width=(StatorVariable.Stator_Lam_Dia-StatorVariable.Stator_Bore-StatorVariable.Slot_Depth)*DoETable.i_YtoT(caseNum);  % 상수
        % StatorVariable.Slot_Opening=StatorVariable.Slot_Width*DoETable.Ratio_SlotOpening_ParallelSlot(caseNum);  % 상수
        % StatorVariable.Sleeve_Thickness=0;  % 상수
        StatorVariable.Ratio_Bore                       =DoETable.Ratio_Bore(CaseNumber);                           % 비율
        StatorVariable.Ratio_SlotDepth_ParallelSlot     =DoETable.Ratio_SlotDepth_ParallelSlot(CaseNumber);  % 비율
        temp_StatorBore                                 =StatorVariable.Stator_Lam_Dia*StatorVariable.Ratio_Bore;  % 계산용
        temp_BackYoke                                   =(StatorVariable.Stator_Lam_Dia-temp_StatorBore)/2*(1-StatorVariable.Ratio_SlotDepth_ParallelSlot);  % 계산용
        temp_Slot_Width_max                             =temp_BackYoke/DoETable.i_YtoT(CaseNumber);  % 계산용
        StatorVariable.Ratio_SlotWidth                  =(temp_StatorBore*pi/StatorVariable.Slot_Number)/temp_Slot_Width_max;  % 비율
        StatorVariable.Ratio_SlotOpening_ParallelSlot   =DoETable.Ratio_SlotOpening_ParallelSlot(CaseNumber);  % 비율
        StatorVariable.Ratio_SleeveThickness            =0;  % 비율, 고정
        
        setMcadVariable(StatorVariable,mcad);
        
        % RotorVariable Struct (그냥 구조체가 아님, 변수 추가하려면 "motorCadGeometryRotor" 내부에서 정의 후 진행)
        RotorVariable                                   =motorCadGeometryRotor(DoETable(CaseNumber,:),FixVariableTable.VMagnet_Layers); 
        RotorVariable.BPMRotor                          =FixVariableTable.BPMRotor;
        RotorVariable.Pole_Number                       =FixVariableTable.Pole_Number;
        RotorVariable.VMagnet_Layers                    =FixVariableTable.VMagnet_Layers;
        % RotorVariable.Banding_Thickness=FixVariableTable.Banding_Thickness;  % 고정
        RotorVariable.Ratio_BandingThickness            =FixVariableTable.Ratio_BandingThickness;  % 고정
        % RotorVariable.Shaft_Dia=FixVariableTable.Shaft_Dia;  % 고정
        temp_Rotor_Dia                                  =StatorVariable.Stator_Lam_Dia*DoETable.Ratio_Bore(CaseNumber)-2*FixVariableTable.Airgap;
        RotorVariable.Ratio_ShaftD                      =FixVariableTable.Shaft_Dia/temp_Rotor_Dia;
        RotorVariable.Shaft_Dia_Front                   =FixVariableTable.Shaft_Dia;  % 샤프트 외경 고정
        RotorVariable.Shaft_Dia_Rear                    =FixVariableTable.Shaft_Dia;  % 샤프트 외경 고정
        RotorVariable.Airgap                            =FixVariableTable.Airgap;  % 고정
        RotorVariable.VShapeMagnetSegments_Array        =FixVariableTable.VShapeMagnetSegments_Array;
        RotorVariable.BridgeThickness_Array             =FixVariableTable.BridgeThickness_Array;        
        setMcadVariable(RotorVariable,mcad);        
        % EtcVariable Struct, Axial parameters...
        EtcVariable=struct();
        % EtcVariable.N_d_MotorLAB=DoETable.N_d_MotorLAB(caseNum);  
        % EtcVariable.Imax_MotorLAB=DoETable.Imax_MotorLAB(caseNum);  
        EtcVariable.Rotor_Lam_Length                    = DoETable.ActiveLength(CaseNumber);
        EtcVariable.Stator_Lam_Length                   = DoETable.ActiveLength(CaseNumber);
        EtcVariable.Magnet_Length                       = DoETable.ActiveLength(CaseNumber);
        EtcVariable.Motor_Length                        = DoETable.ActiveLength(CaseNumber)+100;
        EtcVariable.AxialSegments                       = FixVariableTable.AxialSegments;  % 영구자석 축방향 분할
        
        setMcadVariable(EtcVariable,mcad);
        
         fileName = ['Z:\Simulation\LabProj2023v1\12p72s_VV_HWY\PNG', '\Pic_', 'Radial',num2str(CaseNumber), '.png'];

         mcad.SaveScreenToFile('Radial',fileName)

        %% Winding
        settedConductorData=struct();
        NewConductorData=struct();
        settedConductorData.Armature_CoilStyle          = FixVariableTable.Armature_CoilStyle;          % Coil Style : Hairpin
        settedConductorData.Insulation_Thickness        = FixVariableTable.Insulation_Thickness;        % 도체 절연체 두께
        settedConductorData.Liner_Thickness             = FixVariableTable.Liner_Thickness;             % 절연지 두께
        settedConductorData.WindingLayers               = FixVariableTable.WindingLayers;                % 슬롯 내 턴 수
        settedConductorData.ParallelPaths_Hairpin       = FixVariableTable.ParallelPaths_Hairpin;        % 병렬 수
        % settedConductorData.ConductorsPerSlot         = FixVariableTable.ConductorsPerSlot;            % WindingLayers 에 따라 자동으로 적용됨
        settedConductorData.ConductorSeparation         = FixVariableTable.ConductorSeparation;         % 방사방향 도체 사이 거리
        settedConductorData.temp_fillfactor             = FixVariableTable.temp_fillfactor;             % temp
        settedConductorData.HairpinWindingPatternMethod = FixVariableTable.HairpinWindingPatternMethod; % Improved
        settedConductorData.MagThrow                    = FixVariableTable.MagThrow;                    % 권선 피치
        setMcadVariable(settedConductorData,mcad);
        
        % 형상 적용을 위한 저장
        % mcad.SaveToFile(newMotFilePath);  
        
        % Hair-pin coil
        validGeometry=mcad.CheckIfGeometryIsValid(1);  % Motor-CAD 자체 기능
       % tic
        % if validGeometry==1
            [~,settedConductorData.Area_Slot]                     =mcad.GetVariable('Area_Slot');                  % 슬롯 영역 넓이
            [~,settedConductorData.Area_Winding_With_Liner]       =mcad.GetVariable('Area_Winding_With_Liner');    % 직사각각형 슬롯 영역 넓이
            [~,settedConductorData.Slot_Width]                    =mcad.GetVariable('Slot_Width');                 % 슬롯 너비 (회전방향)
            [~,settedConductorData.Winding_Depth]                 =mcad.GetVariable('Winding_Depth');              % 직사각형 슬롯 깊이 (방사방향)
            NewConductorData=calcConductorSize(settedConductorData, message_on);  % 현재 셋팅된 값 기반으로 copper 사이즈 계산
        % end
                setMcadVariable(NewConductorData,mcad);
% toc
           fileName = ['Z:\Simulation\LabProj2023v1\12p72s_VV_HWY\PNG', '\Pic_', 'StatorWinding',num2str(CaseNumber), '.png'];

             mcad.SaveScreenToFile('StatorWinding',fileName)
    end 
    toc
        tic
        if validGeometry==1
            variable4calcHairPin=McadHairPinVariable([]).Output;
            variable4calcHairPin=getMcadStatorVariable(variable4calcHairPin,mcad);
        end
        toc

        tic
        toc
        if message_on>1
            disp(['case ', num2str(CaseNumber),' setting done'])
        end
        toc
    end
    toc
% end