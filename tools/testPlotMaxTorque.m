filepath='Z:\01_Codes_Projects\Testdata_post\Total_Effy_skew_rework_HDEV.csv';
[dataTable, NameCell]=readDataFile(filepath,40);
speedMeasArray=replaceSimilarData(dataTable.RPM);
torqueMeasArray=replaceSimilarData(dataTable.Torque);
efficiencyMeasArray=dataTable.Efficiency;

[speedArray, BorderTorque] = plotMaxTorque(speedMeasArray, torqueMeasArray);
