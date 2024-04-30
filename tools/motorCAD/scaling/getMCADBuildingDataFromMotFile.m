function BuildingData = getMCADBuildingDataFromMotFile(ActiveXParametersStruct)
    % MOT 파일로부터 ActiveX 파라미터 테이블을 가져옴
    % 구조체 초기화

    Subcategories = {'MotorCADGeo', 'coeffi', 'LabBuildData', 'PostCalcTemp','T0data'};
    for cat = Subcategories
        categories.(cat{1}) = [];
    end

    nonSubcategoris= {'LabBuildData','LossModel'};
    for cat = nonSubcategoris
        noncategories.(cat{1}) = [];
    end


    categories.MotorCADGeo={
    'FEALossMap_RefSpeed_Lab'  ,   
    'SpeedMax_MotorLAB'        ,
    'CurrentSpec_MotorLAB'     ,
    'MaxModelCurrent_MotorLAB',
    'MaxModelCurrent_RMS_MotorLAB',
     };    
    noncategories.LabBuildData ={
    'Twdg_MotorLAB'                  , 
    'ArmatureConductor_Temperature'  , 
    'TwindingCalc_MotorLAB'          , 
    'WindingTemp_ACLoss_Ref_Lab'     , 
    'Tmag_MotorLAB'                  , 
    'TmagnetCalc_MotorLAB'           , 
    'Airgap_Temperature'             , 
    'Bearing_Temperature_F'          , 
    'Bearing_Temperature_R'          ,
    'RacRdc_MotorLAB'                ,
    'LabModel_Saturation_Date'       ,
    'CurrentMotFilePath_MotorLAB'    ,
    'InitialImport_MotorLAB',
    };
     categories.LabBuildData ={
    'CalcTypeCuLoss_MotorLAB'   ,
    'n2ac_MotorLAB'             ,
    'AcLossFreq_MotorLAB'       ,
    'IronLossCalc_Lab'          ,
    'FEALossMap_RefSpeed_Lab'   ,
    'MagnetLossCalc_Lab'        ,
    'MagLossCoeff_MotorLAB'     ,
    'BandingLossCoefficient_Lab',
    'BandingLossCalc_Lab'       ,
     };
     categories.coeffi={
    'HybridAdjustmentFactor_ACLosses'  ,
    'WindingAlpha_MotorLAB'            ,
    'StatorCopperFreqCompTempExponent' ,
    'BrTempCoeff_MotorLAB'             ,    
     };    
     noncategories.LossModel={
    'Resistance_MotorLAB', 
    'EndWindingResistance_Lab', 
    'EndWindingInductance_Lab', 
     };
    categories.PostCalcTemp={
     'TwindingCalc_MotorLAB'     ,
     'TmagnetCalc_MotorLAB'      ,   
    };
    categories.T0data={
    'Twdg_MotorLAB'              ,           
    'Resistance_MotorLAB'        ,           
    'EndWindingResistance_Lab'   ,           
    'ResistanceActivePart'       ,       
    };

    
    %% nonCategories
    BuildingData = struct();    

        NoncategorieNames=fieldnames(noncategories);
    for categoryIndex = 1:length(NoncategorieNames)
        category=NoncategorieNames{categoryIndex};    %% MachineData 변수 종류
        for automationIndex=1:length(noncategories.(category))
        paramName = noncategories.(category){automationIndex};
        MCADVarName=replaceMLABvar2MCADvar(paramName);
        [filteredTable, ~] = findAutomationNameFromAllCategory(ActiveXParametersStruct, MCADVarName);
        % storeData(paramName, filteredTable,category);
        BuildingData=storeStrWithSubStrData(BuildingData,category,paramName, filteredTable);
        end
    end
    
    BuildingData=mergeSubStructs(BuildingData);


    %% Categories
    categorieNames=fieldnames(categories);
    for categoryIndex = 1:length(categorieNames)
        category=categorieNames{categoryIndex};    %% MachineData 변수 종류
        for automationIndex=1:length(categories.(category))
        paramName = categories.(category){automationIndex};
        MCADVarName=replaceMLABvar2MCADvar(paramName);
        [filteredTable, ~] = findAutomationNameFromAllCategory(ActiveXParametersStruct, MCADVarName);
        % storeData(paramName, filteredTable,category);
        BuildingData=storeStrWithSubStrData(BuildingData,category,paramName, filteredTable);
        end
    end
    
    BuildingData=checkMCADLABMaxModelCurrent(BuildingData);



end
