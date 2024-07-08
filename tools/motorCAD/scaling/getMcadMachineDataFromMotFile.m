function MachineData = getMcadMachineDataFromMotFile(ActiveXParametersStruct)
    % MOT 파일로부터 ActiveX 파라미터 테이블을 가져옴
    if ~isstruct(ActiveXParametersStruct)
        ActiveXParametersStruct = getMcadActiveXTableFromMotFile(ActiveXParametersStruct);
    end   % ActiveXParametersStruct = getMcadActiveXTableFromMotFile(MotFilePath);
    
    % Geometry 카테고리
    categories.Geometry = {'Pole_Number', 'Slot_Number', 'DCBusVoltage', 'Stator_Lam_Dia', 'Stator_Lam_Length', 'Motor_Length', 'Housing_Dia'};
    
    % Winding 카테고리
    categories.Winding = {'Armature_CoilStyle','Copper_Diameter','GrossSlotFillFactor','RMSCurrent','NumberStrandsHand','ArmatureConductorLengthPh', 'ArmatureMLT', 'ArmatureEWdgMLT_Calculated', 'Area_Slot', 'Area_Slot_NoWedge', 'Area_Winding_With_Liner', 'ParallelPaths', 'MagThrow', 'WindingLayers', 'HairpinWindingPatternMethod', 'Copper_Width', 'Copper_Height', 'ArmatureConductorCSA', 'MagTurnsConductor', 'ArmatureTurnCSA','RMSCurrentDensity'};

    % Winding Definition 카테고리
    categories.WindingDefinition = {'Insulation_Thickness', 'Liner_Thickness', 'ConductorSeparation'};
    
    % Loss Model and Temperature 카테고리
    categories.LossModelTemperature = {'Resistance_MotorLAB', 'EndWindingResistance_Lab', 'EndWindingInductance_Lab', 'ArmatureConductor_Temperature', 'Twdg_MotorLAB', 'ACConductorLossProportion_Lab', 'NumberOfCuboids_LossModel_Lab'};

    % 구조체 초기화
    MachineData = struct();
    

    % 모든 파라미터 처리
    categorieNames=fieldnames(categories);
    for categoryIndex = 1:length(categorieNames)
        category=categorieNames{categoryIndex};    %% MachineData 변수 종류
        for automationIndex=1:length(categories.(category))
        paramName = categories.(category){automationIndex};
        MCADVarName=replaceMLABvar2MCADvar(paramName);
        [filteredTable, ~] = findAutomationNameFromAllCategory(ActiveXParametersStruct, MCADVarName);
        % storeData(paramName, filteredTable,category);
        MachineData=storeStrWithSubStrData(MachineData,category,paramName, filteredTable);

        end
    end


    % 상세 치수 (Stator)
    RefStatorVariable = McadStatorVariable('');
    StatorVariableListCell = fieldnames(RefStatorVariable);
    for i = 1:length(StatorVariableListCell)
        paramName = StatorVariableListCell{i};
        MCADVarName=replaceMLABvar2MCADvar(paramName);
        [filteredTable, ~] = findAutomationNameFromAllCategory(ActiveXParametersStruct, MCADVarName);
        % storeData(paramName, filteredTable,'StatorVariable');
        MachineData=storeStrWithSubStrData(MachineData,'StatorVariable',paramName, filteredTable);
    end

    % 상세 치수 (Rotor)
    RefRotorVariable = McadRotorVariable('');
    rotorVariableListCell = fieldnames(RefRotorVariable);
    for i = 1:length(rotorVariableListCell)
        paramName = rotorVariableListCell{i};
        MCADVarName=replaceMLABvar2MCADvar(paramName);
        [filteredTable, ~] = findAutomationNameFromAllCategory(ActiveXParametersStruct, MCADVarName);
        % storeData(paramName, filteredTable,'RotorVariable');
        MachineData=storeStrWithSubStrData(MachineData,'RotorVariable',paramName, filteredTable);
    end
    
    % 조건부 실행 및 계산
    if isfield(MachineData.Winding, 'Armature_CoilStyle')
        if MachineData.Winding.Armature_CoilStyle == 1
            disp('HairPin');
           %% ArmatureConductorCSA
            Irms                =MachineData.Winding.RMSCurrent             ;
            ParallelPath        =MachineData.Winding.ParallelPaths          ;    
            Nstrand             =MachineData.Winding.NumberStrandsHand      ;        
            Jrms                =MachineData.Winding.RMSCurrentDensity      ;        
            MachineData.Winding.ArmatureConductorCSA=calcConductorCSAFromJ(Irms,ParallelPath,Nstrand,Jrms);       
            MachineData.Winding.Area4Resistance  =MachineData.Winding.ArmatureConductorCSA;

           
        elseif MachineData.Winding.Armature_CoilStyle == 0
            disp('환선');
            if isfield(MachineData.Winding, 'ArmatureTurnCSA')
                %% 전류, 전류밀도로 역산 (CSA는 도체의 면적)
            Irms                =MachineData.Winding.RMSCurrent             ;
            ParallelPath        =MachineData.Winding.ParallelPaths          ;    
            Nstrand             =MachineData.Winding.NumberStrandsHand      ;        
            Jrms                =MachineData.Winding.RMSCurrentDensity      ;  
            MachineData.Winding.ArmatureConductorCSA=calcConductorCSAFromJ(Irms,ParallelPath,Nstrand,Jrms);
            
            %% 도체 경으로 계산
             MachineData.Winding.ArmatureTurnCSA=calcCircleArea(MachineData.Winding.Copper_Diameter);
            end
        end
    end

    %% 후처리
     MachineData.LossModelTemperature.ResistanceActivePart=MachineData.LossModelTemperature.Resistance_MotorLAB-MachineData.LossModelTemperature.EndWindingResistance_Lab;

 
    % 
    % if isfield(MachineData.Winding, 'RMSCurrent') && isfield(MachineData.Winding, 'ParallelPaths') && isfield(MachineData.Winding, 'NumberStrandsHand') && isfield(MachineData.Winding, 'ArmatureConductorCSA')
    %     MachineData.Winding.RMSCurrentDensity = calcCurrentDensity(MachineData.Winding.RMSCurrent, double(MachineData.Winding.ParallelPaths), double(MachineData.Winding.NumberStrandsHand), MachineData.Winding.ArmatureConductorCSA);
    % end
end
