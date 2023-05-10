function torqueArray=calInvPowerArray(speedArray,powerArray)

torqueArray=powerArray*1000./rpm2radsec(speedArray)
end