% Katech csv
filepath="Z:\01_Codes_Projects\Testdata_post\수소동력 65도 부분부하 효율 평균정리_V5.csv"
[dataTable, NameCell]=readDataFile(filepath,40);
speedMeasArray=replaceSimilarData(dataTable.(3));
torqueMeasArray=replaceSimilarData(dataTable.("Dynamo 토크"));
CurrentMeasArray=dataTable.("U상 전류");

scatter3(speedMeasArray,torqueMeasArray,CurrentMeasArray,'k')
hold on
mesh(Speed,Shaft_Torque,Stator_Current_Line_RMS)
hold on
% contour3(Speed,Shaft_Torque,Stator_Current_Line_RMS, 'EdgeColor', 'k', 'ShowText', 'on', 'TextStep', 2);
xlabel('Speed, [RPM]'); 
ylabel('Torque, [Nm]'); 
zlabel('Current RMS [A]')
formatter_sci