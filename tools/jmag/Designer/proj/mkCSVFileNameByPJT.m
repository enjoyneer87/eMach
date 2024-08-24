function CSVFileNameByPJT=mkCSVFileNameByPJT(app,addName)
    PJTName   =app.GetProjectName;
    portNumber=getPCRDPPortNumber;
    CSVFileNameByPJT=fullfile([PJTName,addName,'_port',num2str(portNumber),'.csv']);

end