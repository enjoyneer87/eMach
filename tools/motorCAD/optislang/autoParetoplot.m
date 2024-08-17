Sensitivity_f3='D:\KangDH\Optislang_Motorcad\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\Sensitivity__f3'
EA_f3_maxtorque='D:\KangDH\Optislang_Motorcad\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd'
csvType='Sensitivity'
csvType='*ea*'
folder = EA_f3_maxtorque
fileList = dir(fullfile(folder, strcat(csvType,'.csv')))

resultTable=readtable(fileList.name);

VariableNames=resultTable.Properties.VariableNames;

constr_cells = strfind(VariableNames, 'temp');
constr_idx = ~cellfun(@isempty, constr_cells);
temperature_cell = VariableNames(constr_idx);

constr_cells = strfind(VariableNames, 'torque');
constr_idx = ~cellfun(@isempty, constr_cells);
torque_cell = VariableNames(constr_idx);

%% DOE

% constr_cell{1}
% resultTable.(constr_cell{1})




%% All Design Table(Optimization)
constr_o_Op2_max_temp = resultTable.(temperature_cell{1}) <= 180;
constr_o_Maxtorque = resultTable.(torque_cell{1}) >= 1200;

feasibleTable = resultTable(constr_o_Op2_max_temp & constr_o_Maxtorque, :);
nonfeasibleTable = resultTable(~constr_o_Op2_max_temp | ~constr_o_Maxtorque, :);

feasiblePlot=scatter(feasibleTable.obj_o_Weight_Act,feasibleTable.obj_o_Wh_Loss);
feasiblePlot.MarkerFaceColor='b';
feasiblePlot.DisplayName='Feasible';
hold on

sc=scatter(nonfeasibleTable.obj_o_Weight_Act,nonfeasibleTable.obj_o_Wh_Loss);
% aAxes=paretofigure.Children;
% sc=aAxes.Children;
sc.DisplayName='NonFeasible';
sc.MarkerEdgeColor='y';

% Paretoset
%% DirectOpti


%% Style
set(gca,'FontName','Times New Roman','FontSize',12)
grid on
legend
ax=gca;
ax.YLabel.String="Driving Cycle Energy Consumtions [Wh]";
ax.XLabel.String="Active Part Weight [kg]";