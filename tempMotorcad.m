mcad = actxserver('MotorCAD.AppAutomation');
[Success,turnsLAB]=mcad.GetVariable('TurnsCalc_MotorLAB')
[Success,turnMag]=mcad.GetVariable('ArmatureTurnsPerCoil')
[Success,turnMagfer]=mcad.GetVariable('TurnsRef_MotorLAB')

i_turnLab=10.5
p_Parallel_Path=4

mcad.SetVariable('TurnsCalc_MotorLAB',i_turnLab)

mcApp=mcad
mcApp.SetVariable("LabThermalCoupling", 0)   
mcApp.SetVariable("OpPointSpec_MotorLAB", 0)                      
mcApp.SetVariable("SpeedDemand_MotorLAB",1700) 
mcApp.SetVariable("TorqueDemand_MotorLAB", 1300) 
mcApp.CalculateOperatingPoint_Lab()                           

[ex, LabOpPoint_ShaftTorque] = mcApp.GetVariable("LabOpPoint_ShaftTorque")    
[ex, ipk] = mcApp.GetVariable("LabOpPoint_StatorCurrent_Line_Peak") 
[ex, beta] = mcApp.GetVariable("LabOpPoint_PhaseAdvance") 
mcad.CalculateMagnetic_Lab()
[ex, o_copper_area] = mcApp.GetVariable('Copper_Area')    
[ex,p_Parallel_Path]=mcApp.GetVariable('ParallelPaths')
o_current_density = (ipk/sqrt(2))* i_turnLab / p_Parallel_Path /o_copper_area
o_current_density = (ipk11t/sqrt(2))* 11 / p_Parallel_Path /o_copper_area
mcApp.SetVariable("LabThermalCoupling_DutyCycle", )                        


ipk11t=ipk
ipk11t, ipk
beta11t=beta