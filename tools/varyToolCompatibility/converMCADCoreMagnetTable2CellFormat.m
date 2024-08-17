% DataImport
function TotalData=converMCADCoreMagnetTable2CellFormat(NO18_1160,materialName)
if nargin==2
TotalData.newMatName=materialName;
else
TotalData.newMatName='NeedAName';
end
%% Physical-Thermal Table
ThermalTable = NO18_1160(contains(NO18_1160.AutomationName,'Thermal Conductivity'),:);
NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName,ThermalTable.AutomationName),:);
ThermalTable = [ThermalTable; NO18_1160(contains(NO18_1160.AutomationName,'Specific Heat'),:)];
NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName,ThermalTable.AutomationName),:);
ThermalTable = [ThermalTable; NO18_1160(strcmp(NO18_1160.AutomationName,'Density'),:)];
Density   =str2double(NO18_1160.Value(strcmp(NO18_1160.AutomationName,'Density')));
NO18_1160 = NO18_1160(~strcmp(NO18_1160.AutomationName,'Density'),:);

ThermalTable.Unit(1) = "W/mK";
ThermalTable.Unit(2) = "J/kgK";
ThermalTable.Unit(3) = "kg/m^3";

    
%% BH Table
ExtrapoleatedBValueTable = filterMCADTableWithAnyInfo(NO18_1160, 'Extrapolation_BValue','AutomationName');
NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName,ExtrapoleatedBValueTable.AutomationName),:);
BValueTable = filterMCADTableWithAnyInfo(NO18_1160, 'BValue[','AutomationName');
NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName,BValueTable.AutomationName),:);
%BValueTable = filterMCADTableWithAnyInfo(BValueTable, 'Extrapolation','AutomationName',1);

ExtrapoleatedHValueTable = filterMCADTableWithAnyInfo(NO18_1160, 'Extrapolation_HValue','AutomationName');
NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName,ExtrapoleatedHValueTable.AutomationName),:);
HValueTable = filterMCADTableWithAnyInfo(NO18_1160, 'HValue[','AutomationName');
NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName,HValueTable.AutomationName),:);

BValueTable.Value = str2double(BValueTable.Value);
HValueTable.Value = str2double(HValueTable.Value);

BHValueTable=table(HValueTable.Value,BValueTable.Value);
BHValueTable.Properties.VariableNames={'HValue','BValue'};
BHValueTable.Properties.VariableUnits={'Amps/m','Tesla'};

ExtrapoleatedBValueTable.Value = str2double(ExtrapoleatedBValueTable.Value);
ExtrapoleatedHValueTable.Value = str2double(ExtrapoleatedHValueTable.Value);



%% Magnetic Table
MagneticTable = NO18_1160(contains(NO18_1160.AutomationName,'MagnetBrValue'),:);
MagneticTable = [MagneticTable; NO18_1160(contains(NO18_1160.AutomationName,'MagneturValue'),:)];
MagneticTable = [MagneticTable; NO18_1160(contains(NO18_1160.AutomationName,'MagnetTempCoefBr'),:)];

NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName,MagneticTable.AutomationName),:);
%% Electrical Table
ElectricalTable = NO18_1160(contains(NO18_1160.AutomationName,'Resistivity'),:);
NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName,ElectricalTable.AutomationName),:);
%% Mechanical Table
MechanicalTable = NO18_1160(contains(NO18_1160.AutomationName,'YoungsCoefficient'),:);
MechanicalTable = [MechanicalTable; NO18_1160(contains(NO18_1160.AutomationName,'PoissonsRatio'),:)];
MechanicalTable = [MechanicalTable; NO18_1160(contains(NO18_1160.AutomationName,'YieldStress'),:)];
MechanicalTable.Unit(1) = "";
MechanicalTable.Unit(2) = "MPa";
MechanicalTable.Unit(3) = "MPa";

NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName,MechanicalTable.AutomationName),:);

%% Steel Loss parameter Table
SteelLossPropertyTable = filterMCADTableWithAnyInfo(NO18_1160, 'Kc','AutomationName');
SteelLossPropertyTable =[SteelLossPropertyTable; filterMCADTableWithAnyInfo(NO18_1160, 'Lamination','AutomationName')];
SteelLossPropertyTable.Value  =str2double(SteelLossPropertyTable.Value);
NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName,SteelLossPropertyTable.AutomationName),:);

%% Steinmetz Loss Table
SteinmetzLossTable=filterMCADTableWithAnyInfo(NO18_1160, '_Steinmetz','AutomationName');
NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName,SteinmetzLossTable.AutomationName),:);

%% Bertotti Maxwell Loss Table
LaminationThickness= SteelLossPropertyTable.Value(contains(SteelLossPropertyTable.AutomationName,'Thick'));
ElectricalResistivity= str2double(ElectricalTable.Value(strcmp(ElectricalTable.AutomationName,'ElectricalResistivity')));


MaxwellLossTable = filterMCADTableWithAnyInfo(NO18_1160, 'Maxwell','AutomationName');
MaxwellLossTable.AutomationName(4)='keddy';
MaxwellLossTable.Value(4)         = (LaminationThickness^2)/(6*Density*ElectricalResistivity);
MaxwellLossTable.AutomationName(5)= 'beta' ;             
MaxwellLossTable.Value(5)= '2'             ; 
MaxwellLossTable.AutomationName(6)= 'EddyLossConstantGammaX' ;             
MaxwellLossTable.Value(6)= '2'           ;     
MaxwellLossTable.AutomationName(7)= 'EddyLossConstantDeltaX' ;             
MaxwellLossTable.Value(7)= '2'           ;     

NO18_1160=NO18_1160(~contains(NO18_1160.AutomationName,MaxwellLossTable.AutomationName),:);
%% Bertotti classic Loss Table
BertottiLossTable=filterMCADTableWithAnyInfo(NO18_1160, 'Bertotti','AutomationName');
kexcessTable=filterMCADTableWithAnyInfo(NO18_1160, 'KexcValue','AutomationName');
BertottiLossTable=[kexcessTable;BertottiLossTable];
NO18_1160=NO18_1160(~contains(NO18_1160.AutomationName,BertottiLossTable.AutomationName),:);
%% Iron Loss Table
% Iron Loss Table
FrequencyTable = filterMCADTableWithAnyInfo(NO18_1160, 'Frequency','AutomationName');
LossDensityTable = filterMCADTableWithAnyInfo(NO18_1160, 'LossDensity','AutomationName');
FluxDensityTable = filterMCADTableWithAnyInfo(NO18_1160, 'FluxDensity','AutomationName');

FrequencyTable.Value = str2double(FrequencyTable.Value);
LossDensityTable.Value = str2double(LossDensityTable.Value);
FluxDensityTable.Value = str2double(FluxDensityTable.Value);
IronLossTable = table(FrequencyTable.Value,LossDensityTable.Value,FluxDensityTable.Value);
IronLossTable.Properties.VariableNames = {'Frequency', 'LossDensity', 'FluxDensity'};
IronLossTable.Properties.VariableUnits = {'Hz', 'kW/kg', 'Tesla'};

NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName, FrequencyTable.AutomationName), :);
NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName, LossDensityTable.AutomationName), :);
NO18_1160 = NO18_1160(~contains(NO18_1160.AutomationName, FluxDensityTable.AutomationName), :);

%% 
TotalData=struct();
TotalData.ThermalTable=ThermalTable;
TotalData.BHValueTable=BHValueTable;
TotalData.SteelLossPropertyTable=SteelLossPropertyTable;
TotalData.SteinmetzLossTable=SteinmetzLossTable;
TotalData.MaxwellLossTable=MaxwellLossTable;
TotalData.BertottiLossTable=BertottiLossTable;
TotalData.IronLossTable=IronLossTable;
TotalData.MagneticTable=MagneticTable;
TotalData.ElectricalTable=ElectricalTable;
TotalData.MechanicalTable=MechanicalTable;
TotalData.Type='MotorCAD';


%%
% TempTable = filterMCADTableWithAnyInfo(NO18_1160, 'Temperature','AutomationName');
% TempTable = filterMCADTableWithAnyInfo(TempTable, 'Valid','AutomationName',1);


% %%
% NonBvalue = filterMCADTableWithAnyInfo(NO18_1160, 'BValue','AutomationName',1);
% NonBHvalue = filterMCADTableWithAnyInfo(NonBvalue, 'HValue','AutomationName',1);
% NonBHTempvalue = filterMCADTableWithAnyInfo(NonBHvalue, 'Temperature','AutomationName',1);

% %% 

% Bvalue=BValueTable.Value;
% Hvalue=HValueTable.Value;
% TempValue=TempTable.Value;
% TotalTable=table(TempValue,Bvalue,Hvalue);
% TotalTable.Properties.VariableUnits=["degC","Tesla","Amps/m"];
% str4DataCellPerTemp  = struct();
% str4DataTablePerTemp = struct();
%     for i = 1:numel(TemperatureData)
%         % 현재 온도에 해당하는 행 선택
%         currentTemp = TemperatureData(i);
%         tempTable = TotalTable(TotalTable.TempValue == currentTemp, :);    
%         % 구조체에 저장
%         if currentTemp<0
%         fieldName = ['DataAtTempMinus', num2str(abs(currentTemp))];
%         else
%         fieldName = ['DataAtTemp', num2str(currentTemp)];
%         end
%         str4DataCellPerTemp.(fieldName) = num2cell([tempTable.Hvalue,tempTable.Bvalue]);
%         str4DataTablePerTemp.(fieldName) = table(tempTable.Hvalue,tempTable.Bvalue);
%         str4DataTablePerTemp.(fieldName).Properties.VariableNames={'Hvalue','Bvalue'};
%         str4DataTablePerTemp.(fieldName).Properties.Description=['Temp=',num2str(currentTemp)];
%     end
    
%     TotalData.str4DataCellPerTemp   =str4DataCellPerTemp;
%     TotalData.str4DataTablePerTemp  =str4DataTablePerTemp;
%     TotalData.NonBHTempTable=NonBHTempvalue;
%     TotalData.TotalTable=TotalTable;
end