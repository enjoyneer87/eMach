function MatFilePath=reNameElecMatDate(Lab1MatFileDir)
   initialMatFileDir       = fullfile(Lab1MatFileDir, 'MotorLAB_elecdata');

    if exist(initialMatFileDir,"file")
        temp_time               = datetime("now");
        matFileDir              = strcat(initialMatFileDir, '_', num2str(temp_time.Hour), 'h', num2str(temp_time.Minute), 'm');    
        initialMatFilePath      = strcat(initialMatFileDir, '.mat');
        MatFilePath             = strcat(matFileDir, '.mat');
        copyfile(initialMatFileDir, MatFilePath);
    end
end