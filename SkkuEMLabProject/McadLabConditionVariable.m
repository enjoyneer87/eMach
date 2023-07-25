%calc option
% OP2thermalCouplingType=2 % 0: no thermal coupling 1: Loss-> Thermal % closed coupled
% OP3thermalCouplingType=1 % 0: no thermal coupling 1: Loss-> Thermal % closed coupled
function variable = McadLabConditionVariable(fileName)

variable=struct();
variable.ModelType_MotorLAB     =2             % Saturation model type: 0 Fixed Inductance 1: singel step 2: Full Cycle
variable.SatModelPoints_MotorLAB=1           % Saturation model: 0 - coarse 1- fine resolution (30 points)
variable.LossModel_Lab          =1        % Loss model type: 1-FEA 2 -custom
variable.BuildSatModel_MotorLAB=1          % Activate saturation model               
variable.BuildLossModel_MotorLAB=1         %% Activate loss model                
variable.CalcTypeCuLoss_MotorLAB=3         % 0 DC only 1 DC+AC(User) 2 DC+AC (FEA single Point) 3 DC+AC (FEA Map)      
variable.ACLossGeneratorMethod_Lab =1      
variable.ProximityLossModel = variable.ACLossGeneratorMethod_Lab;   
variable.IronLossCalc_Lab=3               % 0Neglect 1 OC+SC(User) 2 OC+SC (FEA single Point) 3 (FEA Map)
variable.LabModel_MagnetLoss_Method=3   %0 Neglect 1 User Defined 2 OC+SC (FEA single Point) 3 (FEA Map)         
variable.MagnetLossCalc_Lab =3          % 0 Neglect 1 User Defined 2 OC+SC (FEA single Point) 3 (FEA Map)    

% mcApp.SetVariable("ModelType_MotorLAB", ModelType_MotorLAB)       % Saturation model type: Full Cycle
% mcApp.SetVariable("SatModelPoints_MotorLAB", SatModelPoints_MotorLAB)  % Saturation model: 0 - coarse 1- fine resolution (30 points)  
% mcApp.SetVariable("LossModel_Lab", LossModel_Lab)            % Loss model type: 1-FEA 2 -custom
% mcApp.SetMotorLABContext()                       % Lab context
% mcApp.SetVariable("BuildSatModel_MotorLAB", BuildSatModel_MotorLAB)   % Activate saturation model  
% mcApp.SetVariable("BuildLossModel_MotorLAB", BuildLossModel_MotorLAB)  % Activate loss model  
% mcApp.SetVariable("CalcTypeCuLoss_MotorLAB", CalcTypeCuLoss_MotorLAB)  % 0 DC only 1 DC+AC(User) 2 DC+AC (FEA single Point) 3 DC+AC (FEA Map)
% mcApp.SetVariable("IronLossCalc_Lab", IronLossCalc_Lab)          % 0 Neglect 1 OC+SC(User) 2 OC+SC (FEA single Point) 3 (FEA Map)
% mcApp.SetVariable("LabModel_MagnetLoss_Method", LabModel_MagnetLoss_Method) %0 Neglect 1 User Defined 2 OC+SC (FEA single Point) 3 (FEA Map)
% mcApp.setVariable("MagnetLossCalc_Lab",MagnetLossCalc_Lab) % 0 Neglect 1 OC+SC(User) 2 OC+SC (FEA single Point) 3 (FEA Map

end