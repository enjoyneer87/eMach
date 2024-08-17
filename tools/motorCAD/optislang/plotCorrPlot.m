% correlation matrix 생성
% corr_matrix = corr(randn(100, 5));
SamooHDEVlowfidelitydesignTable=readtable('Z:\Thesis\Optislang_Motorcad\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\Samoo_HDEV_low_fidelity_designTable.csv')
SamooHDEVlowfidelitySensitivit=readtable('Samoo_HDEV_low_fidelity_sensitivity.csv')
SamooHDEVlowfidelitySensitivit=readtable('Z:\Thesis\Optislang_Motorcad\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\Samoo_HDEV_low_fidelity_designTable.csv')

% MOP_f3_2=readtable('CoP matrix_MOP_f3_2_filter_failcase.csv')
% MOP_f3_2.Properties.VariableNames

SamooHDEVlowfidelitySensitivit = removevars(SamooHDEVlowfidelitySensitivit, "o_Op1_Jrms");
SamooHDEVlowfidelitySensitivit = removevars(SamooHDEVlowfidelitySensitivit, ["o_Weight_Mag","o_Weight_Rot_Core","o_Op3_Jrms","o_Op3_copper_area","o_Op3_ipk","o_TorqueVolumeDensity","o_TorqueWeightDensity","o_Op1_copper_area","o_Op1_ipk","o_Op2_Jrms","o_Op2_copper_area","o_Op2_ipk"]);
SamooHDEVlowfidelitySensitivit = removevars(SamooHDEVlowfidelitySensitivit, ["o_Wh_Shaft","o_Wh_input","constr_o_Op2_max_temp","obj_o_Wh_Loss","obj_o_Weight_Act"]);
% plotMOP(MOP_f3_21)

data=SamooHDEVlowfidelitySensitivit;
% unique value의 개수를 계산하여 variation이 없는 variable을 찾기
var_to_delete = [];
for i = 1:size(data, 2)
    if length(unique(data{:, i})) == 1
        var_to_delete = [var_to_delete i];
    end
end

% variation이 없는 variable을 삭제하기
data(:, var_to_delete) = [];
data.Properties.VariableNames = strrep(data.Properties.VariableNames,'_','');

% corrplot 함수 사용
figure
corrplot(data,'type','Pearson','testR','on','varNames',data.Properties.VariableNames)
ax=gcf

%%
for i=1:length(ax.Children)
    t=ax.Children(i).YAxis.Label
    set(t, 'Rotation', 45, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle', 'FontName', 'Times New Roman', 'FontSize', 12);
    ax.Children(i).FontName='Times New Roman'
    if strcmp(class(ax.Children(i).Children(1)),'matlab.graphics.primitive.Text')==1 % ax.Children(i).Children(1)이 text인 경우
        ax.Children(i).Children(1).FontName = 'Times New Roman'; % FontName 속성 값을 'Times New Roman'으로 변경
    end
end

%%
%data의 properties중 이름에 o로 시작하는 propertiesName을 찾고 그중 'oWhLoss','oWeightAct'