% runtests('dimConstructorTest');
% runtests('dimLinearPlusTest');
% runtests('dimLinearMinusTest');
% runtests('dimUminusTest');
% runtests('dimUplusTest');
% runtests('dimMtimesTest');
% runtests('dimDivideTest');
% 
% runtests('xfemmRemoveExtraNodesTest');
% runtests('xfemmRemoveExtraOverlappingArcSegmentsTest');
% runtests('xfemmRemoveExtraOverlappingSegmentsTest');
% runtests('xfemmRemovePartiallyOverlappingArcSegmentsCase1Test');
% runtests('xfemmRemovePartiallyOverlappingArcSegmentsCase2Test');
% runtests('xfemmRemovePartiallyOverlappingArcSegmentsCase3Test');
% runtests('xfemmRemovePartiallyOverlappingArcSegmentsCase4Test');
% runtests('xfemmRemovePartiallyOverlappingSegmentsTest');

%% KDH

findClassUse
fcnDependencyCheck
%%Function Test
runtests("testPlotMaxTorque")
runtests('testDutyCyclePlot')

runtests('testReadExcelFile')
runtests('testreadDataFile')
runtests('testaddIndexToDuplicateCells')
runtests('testReplaceSimilarData')
runtests("testfindTimeVariable")

runtests("testPlotTempRise")
runtests("testplotTempRiseOfPath")
runtests("testPlotMaxtorque")


%% Measured Data
runtests("test_data_pk_beta_map");
runtests("testCompareDataPkBetaMap")
runtests('testPlotEfficiencyContour')
%temp rise
runtests("testTempRise")
runtests("testFindCoolDown")
%% Jmag
runtests("test_data_beta_torque_map");
runtests("test_Jmag_Current_import");
runtests('test_JmagPWMsimulation_import')
runttest('testPlotEffiMap')
%% motorcad
% Lab data mat
runtests('testLossMapMotorcadExport')
runtests('test_data_dq_map_motorcad')
% Post calc

runtest('testFcnCorrectShaftTorque')
% Psi Map
runtests('testDataPkBetaPsiMotorcadExport')
runtests('testDataPkBetaPsiMotorcadperTemp')

% comparison

% surf
runtests('test_data_dq_map_simul')

%% To be checked the result
runtests('calcSideBandHarmonic');

%% To be revised
runtests("test_dq_transform_measured")
runtests('test_dq_transforms_jmag')

runtests('test_data_pk_beta_angle_map_motorcad')

%% Tool
filepath='Z:\01_Codes_Projects\Testdata_post\Total_Effy_skew_rework_HDEV.csv';
[EffiTable, NameCell]=readDataFile(filepath,40);
[varNames, varData]=findVariablebyName(EffiTable,'Torque')
EffiTableNew=renameVariableByName(EffiTable,varNames{1},'Torque')

%% not working
runtests("test_data_dq_map");
runtests('test_data_pk_beta_angle_map_motorcad')
runtests('testDataPkBetaMotorcadMat')

%% working on
runtest('testDataPkBetaLossMotorcadperTemp')

runtests('test_dq_transforms_motorcad')  % line 48 문제 


runtest('fcnCalcDQShaftTorque')
runtest('testSlotVoltagePhasorQuiver')
runtest('testCompareMapSurfContour')

runtests('testCompareEMFMeasuredData')

runtests("genPWMVoltage")
% Class
runtest("testMakeCalibrationMotorCAD")

runtest('exportRawLossMap')
runtest('calcLossMap2CoeffMap')

% 
testPlotForceMap
changeFileNamesEachFolders
getFileNamesFromEachFolders
getForceFileNamesFromEachFolders
getEMFileNamesFromEachFolders
getEMMap
getForceMap
sortMapdataPyleecanMat

% emlab code refactoring
testEMlabcode.m
noteTestEMlabcode.mlx
    testEmlabTNMain
    genMapFluxLinkagePhi
    addCasesJmagDesigner
    submitToScheduler
    runWaitJob
    exportFEMCoilFluxABC
    exportAirGapBField
        SOD_air_SelectWorldPos  % NVH py
        Num_condition_slice % toDo revise
        exportTableDefinition  %  TN
        

    importAirGapBField    d
    sortingJmagTimeBField %  전체 자속밀도데이터에 대해서 일반적인 함수 % ing
    
    sortingBtoAGB 
    transToDQFluxLinkageMapTable


%% Jmag Express
devJmagExpress.mlx

%% Jmag Efficiency Map
devJmagEfficiencyMap.mlx
devJmag3Dthermal.mlx
%% EMLAB Project DOE MotorCAD
runDOEMotorCAD.mlx
draft.mlx