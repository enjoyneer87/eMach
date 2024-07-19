function filteredTable=getMCADLabDataFromMotFile(ActiveXParametersStruct,txtDir)
%% GETMCADLABDATAFROMMOTFILE 
%% [TB] 30Point 외에도 저장하는 코드 만들기
%% MCadActiveXParameter
% activeXstr=loadMCadActiveXParameter();
% ActiveXParametersStruct=activeXstr.ActiveXParametersStruct;
if ~isstruct(ActiveXParametersStruct)&&ischar(ActiveXParametersStruct)
ActiveXParametersStruct=getMcadActiveXTableFromMotFile(ActiveXParametersStruct);
end

%% Check Winding Type
CoilStyle=findMcadTableVariableFromAutomationName(ActiveXParametersStruct.Winding_Design,'Style');
CoilStyle=CoilStyle{:};  % 0== 환선, 1== hairpin;
if CoilStyle==0
conductororCuboidNumbers=findMcadTableVariableFromAutomationName(ActiveXParametersStruct.Calc_Options,'NumberOfCuboids');
conductororCuboidNumbers=str2double(conductororCuboidNumbers);
else
conductororCuboidNumbers=findMcadTableVariableFromAutomationName(ActiveXParametersStruct.Calc_Options,'NumberOfCuboids');
conductororCuboidNumbers=str2double(conductororCuboidNumbers);
end

% ModelParameters_MotorLAB=getMCADTableValueFromActiveXstr(MCadActiveXParameter,'ModelParameters_MotorLAB',mcad(1))
% LossParameters_MotorLAB=getMCADTableValueFromActiveXstr(MCadActiveXParameter,'LossParameters_MotorLAB',mcad(1))
ModelParameters_MotorLAB=filterMCADTableFromActiveXstr(ActiveXParametersStruct,'ModelParameters_MotorLAB');
LossParameters_MotorLAB=filterMCADTableFromActiveXstr(ActiveXParametersStruct,'LossParameters_MotorLAB');
%% Raw Data
% Psi=filterMCADTable(ModelParameters_MotorLAB,'Psi');
Psi = filterMCADTableWithAnyInfo(ModelParameters_MotorLAB, 'Vs','Units');
LHenry = filterMCADTableWithAnyInfo(ModelParameters_MotorLAB, 'Henry','Units');
LHenry =filterMCADTable(LHenry,{'Ld','Lq'});
% Psi=filterMCADTable(Psi,'Psi');
% [dataTable,otherStruct] = createTableFromMCADSatuMapStr(buildData)

% Iron Loss
FEAMapModel= filterMCADTableWithAnyInfo(LossParameters_MotorLAB, 'Lab FEA map model','Description');
% FeLoss= filterMCADTableWithAnyInfo(LossParameters_MotorLAB, 'Coeffi','AutomationName');
FeLoss= filterMCADTableWithAnyInfo(FEAMapModel, 'Fe','AutomationName');
FeLoss=sortrows(FeLoss,"Number","ascend");

% AC Loss
% ACAutoMation = filterMCADTableWithAnyInfo(ACAutoMation, 'Watts','Units')
LossModel_AC_Lab = filterMCADTable(ModelParameters_MotorLAB, 'LossModel_AC_Lab');
% Sleeve Loss
WattsModell = filterMCADTableWithAnyInfo(ModelParameters_MotorLAB, 'Watts','Units');
Current= filterMCADTableWithAnyInfo(ModelParameters_MotorLAB, 'Amps','Units');
PhaseAdvance= filterMCADTableWithAnyInfo(ModelParameters_MotorLAB,'gamma','AutomationName');
BuildInfo= filterMCADTableWithAnyInfo(ModelParameters_MotorLAB,'speed','Description');
ACLossParam = filterMCADTableWithAnyInfo(LossParameters_MotorLAB, 'AC','AutomationName');
% Magnet Loss 
MagnetLoss= filterMCADTableWithAnyInfo(FEAMapModel, 'Mag','AutomationName');
BuildTemp= filterMCADTableWithAnyInfo(ModelParameters_MotorLAB,'°C','Units');
ModelBuildPoints_Gamma_Lab=findAutomationNameFromAllCategory(ActiveXParametersStruct,'ModelBuildPoints_Gamma_Lab');
ModelBuildPoints_Current_Lab=findAutomationNameFromAllCategory(ActiveXParametersStruct,'ModelBuildPoints_Current_Lab');

% ConductorsPerSlot_Total=findAutomationNameFromAllCategory(ActiveXParametersStruct,'ConductorsPerSlot_Total');
HairpinConductors_FEA=findAutomationNameFromAllCategory(ActiveXParametersStruct,'HairpinConductors_FEA');
ConductorCentre_L_y=findAutomationNameFromAllCategory(ActiveXParametersStruct,'ConductorCentre_L_y');
%% 합치기
% mergeTableswithUniqueCheck(Psi,LossModel_AC_Lab)
mcadTable4Txt=vertcat(LHenry,MagnetLoss,FeLoss,ConductorCentre_L_y,HairpinConductors_FEA,ModelBuildPoints_Gamma_Lab,ModelBuildPoints_Current_Lab,ACLossParam,Psi,LossModel_AC_Lab,FEAMapModel,WattsModell,Current,PhaseAdvance,BuildInfo);
mcadTable4Txt=filterMCADTable(mcadTable4Txt,'IM_',1,1);
mcadTable4Txt=filterMCADTable(mcadTable4Txt,'Sync',1,1);
mcadTableNew = filterAndSelectUniqueRows(mcadTable4Txt, 'AutomationName');
%% 데이터 가져오기
% uniqueTable=getMcadTableVariable(mcadTableNew,mcad);
% uniqueTable=getMcadTableVariable(mcadTableNew,mcad(1));
% FeLossTable=getMcadTableVariable(FeLoss,mcad(1));
% FeLossTable.AutomationName
uniqueTable=mcadTableNew;
%% 데이터 정리 
for i=1:height(uniqueTable)
uniqueTable.CurrentValue{i}=convertCharTypeData2ArrayData(uniqueTable.CurrentValue{i});
end
uniqueTable = filterAndSelectUniqueRows(uniqueTable, 'AutomationName');
% ModelParameters_MotorLAB=convertMCADActiveXParameters2MCADVarStruct('ModelParameters_MotorLAB')
mcadTable4TxtBuildValue= filterMCADTableWithAnyInfo(uniqueTable,'<undefined>','Units');
mcadTable4TxtValues= filterMCADTableWithAnyInfo(uniqueTable,'<undefined>','Units',1);
ModelBuildPoints_Current_Lab= getValueFromMCADTablebyName(uniqueTable,'ModelBuildPoints_Current_Lab');
ModelBuildPoints_Current_Lab=ModelBuildPoints_Current_Lab.ModelBuildPoints_Current_Lab;
ModelBuildPoints_Gamma_Lab= getValueFromMCADTablebyName(uniqueTable,'ModelBuildPoints_Gamma_Lab');
ModelBuildPoints_Gamma_Lab=ModelBuildPoints_Gamma_Lab.ModelBuildPoints_Gamma_Lab;

%% 크기별로 데이터 정리
height15Rows2Table = filterMCADTableWithSize(mcadTable4TxtValues, 15, 1);
height30Rows2Table = filterMCADTableWithSize(mcadTable4TxtValues, ModelBuildPoints_Current_Lab*ModelBuildPoints_Gamma_Lab, 1);

if ~isempty(height15Rows2Table)&isempty(height30Rows2Table)
height30Rows2Table=height15Rows2Table;
end

height1Rows2Table = filterMCADTableWithSize(mcadTable4TxtValues, ModelBuildPoints_Current_Lab*ModelBuildPoints_Gamma_Lab, 1);

NonMatchingRows2Table = getTableNonMatchingRowsBetweenTwoTable(mcadTable4TxtValues, 'AutomationName',height30Rows2Table,'AutomationName');
otherheightRows2Table = getTableNonMatchingRowsBetweenTwoTable(NonMatchingRows2Table, 'AutomationName',height1Rows2Table,'AutomationName');
%%  AC Loss Data
LossModel_AC_Lab6Cond=getValueFromMCADTablebyName(otherheightRows2Table,'LossModel_AC_Lab');
OriginAC=LossModel_AC_Lab6Cond.LossModel_AC_Lab;
%% HairPin
% HairpinConductors_FEA=getValueFromMCADTablebyName(uniqueTable,'HairpinConductors_FEA');
% ConductorCentre_L_y=getValueFromMCADTablebyName(uniqueTable,'ConductorCentre_L_y');
% conductorNumbers=length(ConductorCentre_L_y.ConductorCentre_L_y);
%%  conductororCuboidNumbers
if ~isempty(OriginAC)
ACLossTable = convertACLossArray2Table(ModelBuildPoints_Gamma_Lab, ModelBuildPoints_Current_Lab, OriginAC, conductororCuboidNumbers);
end
%%
%% Sorting & Convert Table Format
if ~isempty(height30Rows2Table)
height30Rows2Table=sortrows(height30Rows2Table,"Number","ascend");
ActiveXsatuMapTable=convertMCADActiveXTable2SatuMapTable(height30Rows2Table);
NonZeroTable = removevars(ActiveXsatuMapTable, all(ActiveXsatuMapTable{:,:} == 0));
end
% filteredTable=filterOutTablewithString(NonZeroTable,'Gamma');
% filteredTable=filterOutTablewithString(filteredTable,'Is');
% filteredTable.Stator_Copper_Loss_AC=Stator_Copper_Loss_AC;
% filteredTable=horzcat(filteredTable,AClossTable);
%  Idq & AC Loss Sum
% [NonZeroTable.Id_Peak,NonZeroTable.Iq_Peak]=pkbeta2dq(NonZeroTable.SatModel_Is_Lab,NonZeroTable.SatModel_Gamma_Lab);
[NonZeroTable.Id_Peak,NonZeroTable.Iq_Peak]=pkgamma2dq(NonZeroTable.SatModel_Is_Lab,NonZeroTable.SatModel_Gamma_Lab);
if ~isempty(OriginAC)
filteredTable=horzcat(NonZeroTable,ACLossTable);
%% Calc Total AC
filteredTable = replaceNaNofTable2Zero(filteredTable);
VariableNamesCell = filteredTable.Properties.VariableNames;  % 모든 변수 이름을 가져옵니다.
ACLossCellIndex=contains(VariableNamesCell,'AC Copper Loss');
ACLossCellIs=VariableNamesCell(ACLossCellIndex);
filteredTable.Stator_Copper_Loss_AC=sum(table2array(filteredTable(:, ACLossCellIs)), 2);
else
filteredTable=NonZeroTable;    
end
% Nan2 zero
filteredTable = replaceNaNofTable2Zero(filteredTable);




if nargin>1
disp('Lablink Txt추출용 table입니다.')
filteredTable = reNameLabTable2LabLink(filteredTable);    
end
if nargin>2
    if isfolder(txtDir)
        LabLinkTxtPath=makeLabLinkTXTFromLabTable(filteredTable,txtDir);
    elseif isfile(txtDir)
        LabLinkTxtPath=makeLabLinkTXTFromLabTable(filteredTable,txtDir);
    else 
        LabLinkTxtPath=makeLabLinkTXTFromLabTable(filteredTable);
    end
    disp(['Lablink Txt타입으로', LabLinkTxtPath,'에 txt파일이 export되었습니다.']);
end


end
% p(@plotFitResult, filteredTable);
% 비교대상
% devSatuaMapTable2TXTinLabLinkFormat(newScaledTable,satuMap4.BuildingData.MotorCADGeo,pwd);