filepath="Z:\01_Codes_Projects\Testdata_post\수소동력 65도 부분부하 효율 평균정리_V5.csv"
[dataTable, NameCell]=readDataFile(filepath,40);
speedMeasArray=replaceSimilarData(dataTable.(3));

plot(dataTable.(3))
hold on
plot(speedMeasArray)