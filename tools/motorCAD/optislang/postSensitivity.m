


%%


scatter3(F1.o_LabCurrentJ,F1.obj_o_Weight_Act,F1.o_Maxtorque,'filled')
xlabel('Current Density [A/mm^2]','HorizontalAlignment','center');
ylabel('Active Part Weight [kg]', 'HorizontalAlignment','center');
zlabel('Max Torque[Nm]', 'HorizontalAlignment','center');

%% OP2 Temp 

scatter3(F1.o_Op2_Jrms,F1.o_Weight_Act,F1.o_Op2_max_temp,'filled')
xlabel('Current Density [A/mm^2]','HorizontalAlignment','center');
ylabel('Active Part Weight [kg]', 'HorizontalAlignment','center');
zlabel('Temperature Rise [\circ C]', 'HorizontalAlignment','center');
formatter_sci

%%
scatter3(F1.obj_o_Wh_Loss,F1.obj_o_Weight_Act,F1.o_Op2_max_temp,'filled')
xlabel('Total Loss [Wh]','HorizontalAlignment','center');
ylabel('Active Part Weight [kg]', 'HorizontalAlignment','center');
zlabel('Temperature Rise [\circ C]', 'HorizontalAlignment','center');
formatter_sci