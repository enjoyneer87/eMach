%% Plot J Contour 
% Fig 3.Export J Contour
CurStudyObj=app.GetCurrentStudy;
ModelObj =app.GetCurrentModel
ModelObj.RestoreCadLink
for caseIndex=1:30
    CurStudyObj.SetCurrentCase(caseIndex-1)
    app.View().SetView("SL_Slot5Slot6")
    app.View().SetStep(138)
    app.ExportImageWithSize(['D:/KangDH/Thesis/e10/JMAG/SCL18kc', num2str(1), 'J.png'], 640, 480)
end
CurStudyObj=app.GetCurrentStudy;
for caseIndex=1:30
    CurStudyObj.SetCurrentCase(caseIndex-1)
    app.View().SetView("Slot5Slot6View")
    app.View().SetStep(138)
    app.ExportImageWithSize(['D:/KangDH/Thesis/e10/JMAG/REF18kc', num2str(caseIndex), 'J.png'], 8000, 6000)
end

%% Fig. Slot JLoss 3D
% export Slot J 3D
PartStruct          =getJMAGDesignerPartStruct(app);
PartStruct=getEdgeVertexIdwithXYZCheck(PartStruct,app);   
PartStructByType    =convertJmagPartStructByType(PartStruct);
changeJMAGPartNameTable(PartStructByType.StatorCoreTable,app)


i_Stator_OD=2*max([PartStruct.VertexMaxRPos]);
PartStruct          =getJMAGDesignerPartStruct(app);
idx=findMatchingIndexInStruct(PartStruct,'Name','Stator');
WireStruct=PartStruct(idx);
idx=contains({WireStruct.Name},'StatorCore',IgnoreCase=true);
WireStruct=WireStruct(~idx);

length(WireStruct)
for Index=1:length(WireStruct)
    WireIndex=WireStruct(Index).partIndex;
    [WireStruct(Index).ElementId, WireStruct(Index).NodeID]=devgetMeshData(app,WireIndex);
end
% Babs/Brad/Bt - per time
    % Ref/SC - 동일하니 하나만  - SC가 mesh가 촘촘

%%1) Manual CSV 
% exportData=exportAirGapBField(i_Stator_OD,app)
PartIdList=[WireStruct.partIndex];
exportFilePath=exportFieldData2CSV(app,'Jloss','JEET',PartIdList,'ref','_Load_18k_rgh');

exportFilePath=findCSVFiles(pwd)
LoadexportFilePath=exportFilePath(contains(exportFilePath,'_Load_18k_rgh','IgnoreCase',true));
for CaseIndex=2:length(LoadexportFilePath)
    filePath=LoadexportFilePath{CaseIndex};
    [FieldData{CaseIndex},rawTable]=readJMAGFieldTable(filePath);
end
MatFilePath=strrep(LoadexportFilePath{2},'.csv','Table.mat')
% save(MatFilePath,'FieldData')
load(MatFilePath)


