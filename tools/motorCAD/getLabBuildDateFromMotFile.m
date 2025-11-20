function BuildDate=getLabBuildDateFromMotFile(MotFilePath)
            datacell =getTXTdataScan(MotFilePath);
            BuildDate        = checkMCADMessageLog4LabBuild(datacell);   
end