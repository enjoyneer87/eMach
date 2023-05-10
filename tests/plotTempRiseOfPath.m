function plotTempRiseOfPath(path1)
    path1datas=readDatasfromPath(path1) 
    for i=1:length(path1datas)
        if ~isempty(path1datas{i})
        [PlotMeasured,timeVarNames,xTime] = findTimeVariable(path1datas{i});
        figure(i)
        CANBUSnames={'1. front Bearing up [degC]', '2. front bearing low[degC]', '3. rear bearing up[degC]', '4. rear bearing down[degC]', '5. ambient temp[degC]', '6. NWCend[degC]', '7. NWC end2[degC]', '8. V[degC]', '9. U[degC]', '10. none[degC]', '11. none2[degC]', '12. u slot Inner[degC]', '13. v slot Inner [degC]', '14. w slot Inner[degC]', '15. WC end coil upper[degC]', '16. WC end coil lower[degC]'}
        PlotMeasured.Properties.VariableNames=CANBUSnames;
        plotTempRise(PlotMeasured,xTime)
        ylabel("Temperature [\circ C]")
        xlabel("Time [sec]")
        legend
        end
    end
end



    
