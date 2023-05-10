%% Import Data 
path1='Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\Load\Test_20210909\20210909\온도\';
path2='Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\220516_3차년도 OP시험 데이터\'
motorcadTransientPath='Z:\Thesis\Optislang_Motorcad\CalibrationBEMF\MCAD'
path20210909='Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\Load\Test_20210909\20210909\온도'
path20220516='Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\220516_3차년도 OP시험 데이터\'


path1_strc=dir(path1)
path1_file = string.empty;
for i=1:length(path1_strc)
    path1_file(i,1) = string(path1_strc(i).name);
end

path2_strc=dir(path2)
path2_file = string.empty;
for i=1:length(path2_strc)
    path2_file(i,1) = string(path2_strc(i).name);
end

pathMotorcCAD_strc=dir(motorcadTransientPath)
pathMotorCAD_file = string.empty;
for i=1:length(pathMotorcCAD_strc)
    pathMotorCAD_file(i,1) = string(pathMotorcCAD_strc(i).name);
end
%% read
PlotMeasured=readDataFile(fullfile(path1,path1_file(5)),40);
% filepath=fullfile(motorcadTransientPath,pathMotorCAD_file(4))
% NumVariables=900
PlotSimulatead=readDataFile(fullfile(motorcadTransientPath,pathMotorCAD_file(4)),40);
% PlotSimulatead=readDatasfromPath(motorcadTransientPath);

%% Check Time Column
[PlotMeasured,timeVarNames,xTime]=findTimeVariable(PlotMeasured);




%% Change VariableNames
CANBUSnames={'1. front Bearing up [degC]', '2. front bearing low[degC]', '3. rear bearing up[degC]', '4. rear bearing down[degC]', '5. ambient temp[degC]', '6. NWCend[degC]', '7. NWC end2[degC]', '8. V[degC]', '9. U[degC]', '10. none[degC]', '11. none2[degC]', '12. u slot Inner[degC]', '13. v slot Inner [degC]', '14. w slot Inner[degC]', '15. WC end coil upper[degC]', '16. WC end coil lower[degC]'}
PlotMeasured.Properties.VariableNames=CANBUSnames;
fcnCoolDownPlot(PlotMeasured,xTime)

%% Plot by Type
plotTempRise(PlotMeasured,xTime);


path1datas=readDatasfromPath(path1);
plotTempRiseOfPath(path1)

%% Measured Weight Check
measuredWeights=struct();
measuredWeights.rotorAssy=65.10
measuredWeights.rotorCore=0
measuredWeights.shaft=10.2
measuredWeights.Bearing=2.7;

measuredWeights.statorAssy=
measuredWeights= calculateRotorWeights(measuredWeights)

%% 20220516
OPTest3rdfilename='수소동력 3차년도_OP 시험데이터_20220516.xlsx'
OP_20220516path=fullfile(path20220516,OPTest3rdfilename);
OP_20220516=readExcelFile(fullfile(path20220516,OPTest3rdfilename));
OP_20220516{2}.Properties.VariableUnits;
%% Split By Unit
[tablesplit, name, units]=splitTableByUnits(OP_20220516{2});

%% Plot 
PlotMeasured=OP_20220516{1}

[PlotMeasured,timeVarNames,xTime]=findTimeVariable(OP_20220516{3});
figure(2)
for i=1:width(PlotMeasured)
    varname=PlotMeasured.Properties.VariableNames{i};
    if all(PlotMeasured.(varname))>0 && contains(varname, 'degC') && contains(varname, 'Average') %%%%% 중요
        plot(PlotMeasured.(timeVarNames{2}),PlotMeasured.(varname),'DisplayName',strrep(varname, '_', ' '))
        hold on
        % displayName으로 넣을 이름 설정
        name = strrep(varname, '_', ' ');
        % x, y값 설정
        x = PlotMeasured.(timeVarNames{2})(end-10);
        y = PlotMeasured.(varname)(end-10);
        % NaN이 아닌 가장 마지막 값으로 x, y 좌표 설정
        if isnan(x) || isnan(y)
            idx = find(~isnan(PlotMeasured.Time_1), 1, 'last');
            x = PlotMeasured.(timeVarNames{2})(idx);
            y = PlotMeasured.(varname)(idx-180);
        end
        % text 추가
        text(x, y, name, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle')
    end
end

ylabel("Temperature [\circ C]")
xlabel("Time [sec]")
legend


formatter_sci

load('EffimapMeasureInfo.mat')
m1no1=gcf;
m1no1.Position=figInfo.size;
%% CanBUS Name


%% TimeTable로 변환 ?
% OP2_20210909=table2timetable(OP2_20210909)
% time_step=seconds(OP2_20210909.Times(2)-OP2_20210909.Times(1))
% OP2_20210909.Properties.VariableNames

%% Find Winding data
% col_names={'1 front Bearing up','2 front bearing low','3 rear bearing up', '4 rear bearing down',    '5 End space temp', '6 DE(NC)end','7 DE(NC)end2','8 V end','9 U end','none','none2','10 u active','11 v active', '12 w active','13 WC end coil upper', '14 WC end coil lower'}
% OP2_20210909.Properties.VariableNames=col_names;
% 
% OP2_20210909=table2timetable(OP2_20210909,'TimeStep',time_step,"StartTime",seconds(0));
% 
% figure(f)
% for i=2:width(OP2_20210909)
%     if OP2_20210909.(OP2_20210909.Properties.VariableNames{i})>0
%     plot(OP2_20210909.(1),OP2_20210909.(OP2_20210909.Properties.VariableNames{i}),'DisplayName',OP2_20210909.Properties.VariableNames{i})
%     hold on
%     ylabel("Temperature [\circ C]")
%     xlabel("Time [sec]")
%     end
% end



