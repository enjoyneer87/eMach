function createCustomMagnetJMAG(new_material_name,JDesigner)

%% 'Customized Magnet material
% new_material_name='FeNGen2';
% libPath = 'Custom Materials';   %Path in the [Custom Materials] folder from Material database  
% JDesigner.GetMaterialLibrary().CreateCustomMaterial(new_material_name, libPath);
create_new_material=JDesigner.GetMaterialLibrary().GetUserMaterial(new_material_name);

%% Magnetic properties
create_new_material.SetValue('MagneticPropertyType', 1); %0 or MagneticSteel / 1 or Magnet / 2 or MagnetizationMaterial 
create_new_material.SetValue('MagnetPermeabilityType', 3); 
% create_new_material.GetTable('DemagTemperatureTable').SetName('Demagnetization Table'); 
%523445117 curve = [25, 300000, 1.5, 1.1, 70, 180000];  %A/m  8957 a330
% create_new_material.GetTable('DemagTemperatureTable').SetTable([num2cell(curve)]); 
% magnet_mat=strtrim(new_material_name);     


end