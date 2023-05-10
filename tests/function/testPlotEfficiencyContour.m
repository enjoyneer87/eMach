% Katech csv
filepath="Z:\01_Codes_Projects\Testdata_post\수소동력 65도 부분부하 효율 평균정리_V5.csv"
[dataTable, NameCell]=readDataFile(filepath,40);
speedMeasArray=replaceSimilarData(dataTable.(3));
torqueMeasArray=replaceSimilarData(dataTable.("Dynamo 토크"));
efficiencyMeasArray=dataTable.("모터 효율");
contour1Measured=plotEfficiencyContour(speedMeasArray,torqueMeasArray,efficiencyMeasArray);
