
[cleanedMatrix,normalizedTable]=normlizeDOETable(Sensitivity1);

boxplot(cleanedMatrix, 'Labels', normalizedTable.Properties.VariableNames);
ylabel('Normalized Value except relative error[p.u]')

%% 
%% ST Dia Table 가져오기
num_designs=height(Sensitivity1);
for i = 1:num_designs
    for j = 1:num_designs
        if i ~= j
            kRadialMatrix(i, j) =Sensitivity1.i_Stator_OD(i) /Sensitivity1.i_Stator_OD(j) ;
        end
    end
end
% 
% Sensitivity1Radial = removevars(Sensitivity1Radial, "L1_Pole_Arc");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "L1_Web_Thickness");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "L1_Web_Length");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "i_TurnLab");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "L1_Magnet_Post");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "L1_Magnet_Bar_Width");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "L2_Pole_Arc");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "L1_Pole_V_angle");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "i_Active_Length");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "i_Split_Ratio");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "L2_Web_Thickness");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "i_Depth_Slot_Ratio");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "i_Tooth_Width_Ratio");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "L2_Web_Length");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "i_Slot_Op_Ratio");
% Sensitivity1Radial = removevars(Sensitivity1Radial, "i_YtoT");

Sensitivity1Radial=Sensitivity1