function adjustAxisLimit(xscale,yscale)
    xLimData=xlim;
    yLimData=ylim;
    xlim([xLimData(1), xscale*xLimData(2)]);
    ylim([yLimData(1),yscale*yLimData(2)]);
end