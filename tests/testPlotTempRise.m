path1='Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\Load\Test_20210909\20210909\온도\';
path1_strc=dir(path1)

path1_strc=dir(path1)
path1_file = string.empty;
for i=1:length(path1_strc)
    path1_file(i) = string(path1_strc(i).name);
end



for j=1:length(path1_strc)
    if contains(lower(path1_strc(j).name), '.csv') || contains(lower(path1_strc(j).name), ".xlsx")
        % csv나 xlsx 파일이름이 포함되어 있다면 실행할 코드 작성
    OP2_20210909FileName=path1_strc(j).name
    OP2_20210909=readDataFile(fullfile(path1,OP2_20210909FileName),40);
    %     figure(j)
    end
end


PlotMeasured=OP2_20210909;
[PlotMeasured,timeVarNames,xTime]=findTimeVariable(PlotMeasured);


CANBUSnames={'1. front Bearing up [degC]', '2. front bearing low[degC]', '3. rear bearing up[degC]', '4. rear bearing down[degC]', '5. ambient temp[degC]', '6. NWCend[degC]', '7. NWC end2[degC]', '8. V[degC]', '9. U[degC]', '10. none[degC]', '11. none2[degC]', '12. u slot Inner[degC]', '13. v slot Inner [degC]', '14. w slot Inner[degC]', '15. WC end coil upper[degC]', '16. WC end coil lower[degC]'}
PlotMeasured.Properties.VariableNames=CANBUSnames;
plotTempRise(PlotMeasured,xTime)


