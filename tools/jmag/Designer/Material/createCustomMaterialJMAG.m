function createCustomMaterialJMAG(JDesigner, property,newMatName)
%% Check property Format
if isfield(property, 'MatName')
   property.Type='Syre';
end

if strcmp(property.Type,'Syre')
    BH_curve(:, [1, 2]) = property.BH(:, [2, 1]);
    if isfield(property, 'kh')  %% kh : hysteresis loss coefficient
        property.kh = 0;
    end
    if isfield(property, 'ke')  %% ke : eddy current loss coefficient
        property.ke = 0;
    end
    if isfield(property, 'alpha') %% alpha : hysteresis loss exponent
        property.alpha = 0;
    end
    if isfield(property, 'beta') %% beta : eddy current loss exponent
        property.beta = 0;
    end
    if isfield(property, 'gamma') %% gamma : hysteresis loss exponent
        property.gamma = 0;
    end
    if isfield(property, 'delta') %% delta : eddy current loss exponent
        property.delta = 0;
    end
    if ~isfield(property, 'resistivity') %% resistivity : resistivity
       new_resistivity =1.673e-08;  %ohm.m   
    end

elseif strcmp(property.Type,'MotorCAD')
    BH_curve= property.BHValueTable.Variables;
    new_resistivity = property.ElectricalTable.Value(strcmp(property.ElectricalTable.AutomationName,'ElectricalResistivity'));
else
    error('Error: Material type is not defined')
end
%% Check newMatName
if nargin < 3
    newMatName =[property.MatName,property.Type, 'CustomMaterial'];
end

%% pre-define variables
libPath    ='Custom Materials';
%% Create Custom Material
% MatLib=JDesigner.GetMaterialLibrary()
% Mat=PWMStudyObj.GetMaterialByIndex(0)
% PWMStudyObj.GetMaterialAttributeParameters()
% Mat.GetName()
% Mat.GetMaterial
% sampleMat=MatLib.GetMaterial(1)
% sampleMat.IsValid
% sampleMat.GetPropertyType
% MatJMAGPropTable=sampleMat.GetPropertyTable();
% MatJMAGPropTable = convertChar2JMAGPropertiesTable(MatJMAGPropTable);
% save('MatJMAGPropTable','MatJMAGPropTable')
MatLibObj=JDesigner.GetMaterialLibrary();
if ~MatLibObj.GetMaterial(newMatName).IsValid
JDesigner.GetMaterialLibrary().CreateCustomMaterial(newMatName, libPath);
end
create_new_material=JDesigner.GetMaterialLibrary().GetUserMaterial(newMatName);
create_new_material.SetValue('Manufacturer', 'Customer');
create_new_material.SetValue('Category', 'Semi-Magnetic');
%% Magnetic properties
create_new_material.SetValue('MagneticPropertyType', 'MagneticSteel'); %0 or MagneticSteel / 1 or Magnet / 2 or MagnetizationMaterial 
create_new_material.SetValue('IsotropicType', 'Isotropic');% Material type : 0 or Isotropic / 1 or Anisotropic
create_new_material.SetValue('MagneticSteelPermeabilityType', 'BHCurve');   

%% Magnetic steel permeability type: % 0 or LinearConstant
% 1 or LinearThermalDependency% 2 or BHCurve% 3 or BMCurve% 4 or BMurCurve
% 5 or StressDependency% 6 or MagneticSteelUserSubroutine% 7 or TemperatureDependencyBHCurve
create_new_material.GetTable('BhTable').SetName('BH_MyNewMaterial'); % BH curve name
create_new_material.GetTable('BhTable').SetTable([num2cell(BH_curve)]); % set BH curve data
%% Electric properties
create_new_material.SetValue('ConductivityType', 1);
create_new_material.SetValue('Resistivity', new_resistivity);
%% Loss properties
%IronLoss_type = 1 = IronLossFomula
if strcmp(property.Type,'syre')
    create_new_material.SetValue('Loss_Type', 1);
    create_new_material.SetValue('LossConstantKhX', property.kh);
    create_new_material.SetValue('LossConstantAlphaX', property.alpha);
    create_new_material.SetValue('LossConstantBetaX', property.beta);
    create_new_material.SetValue('LossConstantKeX', property.ke);
    create_new_material.SetValue('LossConstantGammaX', 2.0);
    create_new_material.SetValue('LossConstantDeltaX', 2.0);
elseif strcmp(property.Type,'MotorCAD')
    MaxwellLossTable=property.MaxwellLossTable     ;
    MaxwellLossTable.Value=str2double(MaxwellLossTable.Value) ;

    kh                  = MaxwellLossTable.Value(contains(MaxwellLossTable.AutomationName,'Kh'));
    alpha               = MaxwellLossTable.Value(contains(MaxwellLossTable.AutomationName,'alpha'));
    beta                = MaxwellLossTable.Value(contains(MaxwellLossTable.AutomationName,'beta'));
    keddy                  = MaxwellLossTable.Value(contains(MaxwellLossTable.AutomationName,'keddy'));
    LossConstantGammaX  = MaxwellLossTable.Value(contains(MaxwellLossTable.AutomationName,'LossConstantGammaX'));
    LossConstantDeltaX  = MaxwellLossTable.Value(contains(MaxwellLossTable.AutomationName,'LossConstantDeltaX')); 

    create_new_material.SetValue('Loss_Type', 1);
    create_new_material.SetValue('LossConstantKhX', kh);
    create_new_material.SetValue('LossConstantAlphaX', alpha);
    create_new_material.SetValue('LossConstantBetaX', beta);
    create_new_material.SetValue('LossConstantKeX', keddy);
    create_new_material.SetValue('LossConstantGammaX', LossConstantGammaX);
    create_new_material.SetValue('LossConstantDeltaX', LossConstantDeltaX);
end
% IronLoss_type =0
% IronLoss_Type =2

end