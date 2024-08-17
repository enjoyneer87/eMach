% mcApp = actxserver('MotorCAD.AppAutomation');
% mcApp.LoadFromFile('Z:\Thesis\Optislang_Motorcad\Validation\HDEV_Model2.mot')
% mcApp.DoWeightCalculation()                                          
% [a, initialValue.obj_o_Weight_Act]=mcApp.GetVariable("Weight_Calc_Total") 
% % [a, initialValue.obj_o_Weight_Act]=mcApp.GetVariable("Pole_Number")     

sensitivityTable=readtable('Z:\Thesis\Optislang_Motorcad\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\Samoo_HDEV_low_fidelity_sensitivity.csv');
lowfidel_OptiPareto=readtable('Z:\Thesis\Optislang_Motorcad\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\Samoo_HDEV_low_fidelity_design_table.csv');
lowfidel_designtable=readtable('Z:\Thesis\Optislang_Motorcad\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\Samoo_HDEV_low_fidelity_designTable.csv');

lowfidel_designtable_true=readtable('Z:\Thesis\Optislang_Motorcad\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\Samoo_HDEV_low_fidelity_design_table_true.csv');
lowfidel_designtable_pareto=readtable('Z:\Thesis\Optislang_Motorcad\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\Samoo_HDEV_low_fidelity_pareto.csv');
directDesigntable=readtable('Z:\Thesis\Optislang_Motorcad\HDEV_Code3\OPD\HDEV_ob2o24i28si1f1.py.opd\DirectOpti_HDEV_low_fidelity_designTable.csv');

% initialValue.obj_o_Weight_Act=43.75+20.45+41.15+5.099+9.919;
% initialValue.obj_o_Wh_Loss=641.73;
% initialValue.dutyCycleTemp=78;

% %% Initial Value
% grayColor = [.7 .7 .7];
% 
% paretofigure=figure(1)
% 
% 
% initialPlot=scatter(initialValue.obj_o_Weight_Act,initialValue.obj_o_Wh_Loss);
% initialPlot.DisplayName='Initial Design'
% initialPlot.MarkerFaceColor='y';
% hold on


%% DOE
sensTablePlot=scatter(sensitivityTable.obj_o_Weight_Act,sensitivityTable.obj_o_Wh_Loss);
sensTablePlot.DisplayName='DOE';
sensTablePlot.MarkerEdgeColor=grayColor;
hold on
%% All Design Table(Optimization)
% legend
% feasiblePlot=scatter(lowfidel_designtable_true.obj_o_Weight_Act,lowfidel_designtable_true.obj_o_Wh_Loss);
% feasiblePlot.MarkerFaceColor='b';
% feasiblePlot.DisplayName='Feasible';
% hold on

%%
legend
feasiblePlot=scatter(lowfidel_designtable.obj_o_Weight_Act,lowfidel_designtable.obj_o_Wh_Loss);
feasiblePlot.MarkerFaceColor='b';
feasiblePlot.DisplayName='Feasible';
hold on


% %% NonFeasible
% 
% 
% sc=scatter(lowfidel_OptiPareto.obj_o_Weight_Act,lowfidel_OptiPareto.obj_o_Wh_Loss);
% % aAxes=paretofigure.Children;
% % sc=aAxes.Children;
% sc.DisplayName='NonFeasible';
% sc.MarkerEdgeColor='y';
% hold on
%% DirectOpti
directDesigntable(directDesigntable.obj_o_Wh_Loss == 0,:) = [];
Do=scatter(directDesigntable.obj_o_Weight_Act,directDesigntable.obj_o_Wh_Loss)
Do.MarkerEdgeColor='g';
Do.DisplayName='Direct Optimization'

hold on
%% Paretoset
lowfidel_designtable_paretoPlot=plot(lowfidel_designtable_pareto.obj_o_Weight_Act,lowfidel_designtable_pareto.obj_o_Wh_Loss);
lowfidel_designtable_paretoPlot.Color='r';
lowfidel_designtable_paretoPlot.Marker='*';
lowfidel_designtable_paretoPlot.DisplayName='Pareto'



%% Style
set(gca,'FontName','Times New Roman','FontSize',12)
grid on
legend
ax=gca;
ax.YLabel.String="Driving Cycle Energy Consumtions [Wh]";
ax.XLabel.String="Active Part Weight [kg]";


%% CoP

CoPPlot=heatmap(CoPMatrix);
% CoPPlot.Colormap='parula'

%% Sensitivity

%%parallel plot
paraplot=parallelplot(lowfidel_designtable);
paraplot=parallelplot(sensitivityTable,'LineWidth',0.2,GroupVariable='Pareto');
sensitivityTable = removevars(sensitivityTable, ["i_BuildLineCurrentRMS"]);
sensitivityTable = removevars(sensitivityTable, ["constr_o_Op2_max_temp","obj_o_Wh_Loss","obj_o_Weight_Act"]);
sensitivityTable = removevars(sensitivityTable, ["o_Op1_copper_area","o_Op2_copper_area","o_Op1_ipk","o_Op2_ipk","o_Op3_copper_area","o_Op3_ipk","o_TorqueWeightDensity","o_Wh_Shaft"]);
formatter_sci
hold on

paraaxes=gca()
paraaxes.CoordinateVariables