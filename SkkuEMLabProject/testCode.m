   % tic
    for CaseNumber=1:10
        %% StatorVariable Struct
        StatorVariable.Tooth_Tip_Angle                  =DoETable.Tooth_Tip_Angle(CaseNumber);  % 상수
        StatorVariable.Ratio_Bore                       =DoETable.Ratio_Bore(CaseNumber);                           % 비율
        StatorVariable.Ratio_SlotDepth_ParallelSlot     =DoETable.Ratio_SlotDepth_ParallelSlot(CaseNumber);  % 비율    
        temp_StatorBore                                 =StatorVariable.Stator_Lam_Dia*StatorVariable.Ratio_Bore;  % 계산용
        temp_BackYoke                                   =(StatorVariable.Stator_Lam_Dia-temp_StatorBore)/2*(1-StatorVariable.Ratio_SlotDepth_ParallelSlot);  % 계산용
        temp_Slot_Width_max                             =temp_BackYoke/DoETable.i_YtoT(CaseNumber);  % 계산용
     
        StatorVariable.Ratio_SlotWidth                  =(temp_StatorBore*pi/StatorVariable.Slot_Number)/temp_Slot_Width_max;  % 비율
        StatorVariable.Ratio_SlotOpening_ParallelSlot   =DoETable.Ratio_SlotOpening_ParallelSlot(CaseNumber);  % 비율
        [uniqueStruct1,uniqueStruct2]=findUniqueFields(StatorVariable,tempStator);
        setMcadVariable(StatorVariable,mcad);        
        %% RotorVariable Struct (그냥 구조체가 아님, 변수 추가하려면 "motorCadGeometryRotor" 내부에서 정의 후 진행)
        RotorVariable                                   =motorCadGeometryRotor(DoETable(CaseNumber,:),RotorVariable.VMagnet_Layers); 
        temp_Rotor_Dia                                  =StatorVariable.Stator_Lam_Dia*DoETable.Ratio_Bore(CaseNumber)-2*FixedVariable.Airgap;
        RotorVariable.Ratio_ShaftD                      =FixedVariable.Shaft_Dia/temp_Rotor_Dia;             
        setMcadVariable(RotorVariable,mcad);        
        %% EtcVariable Struct, Axial parameters...
        EtcVariable=struct();
        EtcVariable.Rotor_Lam_Length                    = DoETable.ActiveLength(CaseNumber);
        EtcVariable.Stator_Lam_Length                   = DoETable.ActiveLength(CaseNumber);
        EtcVariable.Magnet_Length                       = DoETable.ActiveLength(CaseNumber);
        EtcVariable.Motor_Length                        = DoETable.ActiveLength(CaseNumber)+100;
        setMcadVariable(EtcVariable,mcad);       
        %% ScreenShoot
        PNGPath  = fullfile(parentPath,'PNG');
        if exist(PNGPath,'dir')==0
            mkdir(PNGPath);
        end
        fileName = [parentPath,'\PNG\',  'Radial_',num2str(CaseNumber), '.png'];
        mcad.SaveScreenToFile('Radial',fileName);

        %% Set Hair-pin coil
        validGeometry=mcad.CheckIfGeometryIsValid(1);  % Motor-CAD 자체 기능
        NewConductorData=struct();

        if validGeometry==1           
            settedConductorData=McadHairPinVariable([]).Output;          
            [mergedStruct,duplicD]=mergeStructs(refFileHairPinData,settedConductorData)                ;
            [~,mergedStruct.Area_Slot]                     =mcad.GetVariable('Area_Slot');                  % 슬롯 영역 넓이
            [~,mergedStruct.Area_Winding_With_Liner]       =mcad.GetVariable('Area_Winding_With_Liner');    % 직사각각형 슬롯 영역 넓이
            [~,mergedStruct.Slot_Width]                    =mcad.GetVariable('Slot_Width');                 % 슬롯 너비 (회전방향)
            [~,mergedStruct.Winding_Depth]                 =mcad.GetVariable('Winding_Depth');              % 직사각형 슬롯 깊이 (방사방향)
            [mergedStruct,duplicD]=mergeStructs(mergedStruct,runSetting.FixedVariable);
            NewConductorData=calcConductorSize(mergedStruct);  % 현재 셋팅된 값 기반으로 copper 사이즈 계산
            setMcadVariable(NewConductorData,mcad);
            fileName = [parentPath,'\PNG\',  'StatorWinding',num2str(CaseNumber), '.png'];    
        %% 형상 적용을 위한 저장
        % mcad.SaveToFile(newMotFilePath);  
        end
        mcad.SaveScreenToFile('StatorWinding',fileName);
    end 
    % toc