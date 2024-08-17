function [o_Wh_Loss] = funDrivingDuty(ext_Duty_Cycle,OSL_PROJECT_DIR,Design_Name, OSL_DESIGN_NAME)
    ref_Duty_Cycle = fullfile(fileparts(fileparts(OSL_PROJECT_DIR)), 'DutyCycleData', strcat(ext_Duty_Cycle{1}, '.dat'));
    refdir = fullfile(fileparts(fileparts(OSL_PROJECT_DIR)), 'MCAD');    
    mot_file_ref_path = fullfile(refdir, strcat(Design_Name, '.mot'));  % Path to the reference *.mot file
    mot_file_new_path = fullfile(wdir, strcat(Design_Name, '_', num2str(OSL_DESIGN_NAME), '.mot'));  % Path to the new *.mot file

    mcApp = actxserver('MotorCAD.AppAutomation');
    
    mcApp.LoadDutyCycle(ref_Duty_Cycle)
%     mcApp.SetVariable('TurnsCalc_MotorLAB', turns)           
    mcApp.SetVariable("LabThermalCoupling_DutyCycle", 0)     
    mcApp.SetVariable("LabThermalCoupling", 0)               
    mcApp.SetVariable('InitialTransientTemperatureOption',4)
    mcApp.SetVariable('InitialHousingTemperature',65)
    mcApp.SetVariable('InitialHousingTemperature',65)
    mcApp.SetVariable('InitialStatorTemperature',140)
    mcApp.SetVariable('InitialWindingTemperature',160)
    mcApp.SetVariable('InitialRotorTemperature',100)
    mcApp.SetVariable('InitialMagnetTemperature',130)
    mcApp.CalculateDutyCycle_Lab()
%      Calculation & Post processing
    ex, o_Wh_Loss = mcApp.GetVariable("DutyCycleTotalLoss")   
    ex, o_Wh_Shaft = mcApp.GetVariable("DutyCycleTotalEnergy_Shaft_Output")   
    ex, o_Wh_input = mcApp.GetVariable("DutyCycleTotalEnergy_Electrical_Input")  
end
