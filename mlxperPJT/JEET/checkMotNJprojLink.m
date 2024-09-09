function [refMSjprojPath] = checkMotNJprojLink(MotFilePath,refMSjprojPath,app)
    % refPath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\e10_UserRemesh.mot';
    if ~exist(MotFilePath,"file")
        MotFilePath='D:\KangDH\Thesis\e10\refModel\e10_UserRemesh.mot';
    end
    [refDIR,FileName,~]=fileparts(MotFilePath);
    dxfFiles = findDXFFiles(refDIR)';
    
    % app=callJmag;
    app.Show
    % refMSjprojPath='Z:/Simulation/JEETACLossValid_e10_v24/refModel/e10_v24.jfiles';
    [~,jprojName,~]=fileparts(refMSjprojPath);
    
    jprojFiles=app.GetProjectFolderPath;
    
    if ~exist(refMSjprojPath,"file")
        refMSjprojPath=fullfile(refDIR,[jprojName,'.jproj']);
    end
    if contains(jprojFiles,'C:/Users/','IgnoreCase',true)
        if ~exist(jprojPath,"file")
        app.SaveAs(jprojPath)
        end
    end
end