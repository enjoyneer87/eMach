function powerArray=calcPowerArray(speedArray,torqueArray)

powerArray=rpm2radsec(speedArray).*torqueArray/1000;

end