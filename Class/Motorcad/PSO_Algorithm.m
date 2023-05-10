function [Total_Population, Total_GlobalBest] = PSO_Algorithm(Optimization_Enviroment)

%% Population
empty_Population.Position = [];
empty_Population.Velocity = [];

if Optimization_Enviroment.Cost_Function == "JMAG"
    for i = 1:size(Optimization_Enviroment.Objective_Function,2)
        
        gen_obj_function = "empty_Population." + Optimization_Enviroment.Objective_Function(i) + "=[];" ;
        eval(gen_obj_function);
        clearvars gen_obj_function
    end
end

if Optimization_Enviroment.Cost_Function == "MotorCad"
    for i = 1:size(Optimization_Enviroment.Objective_Function,2)
        
        gen_obj_function = "empty_Population." + Optimization_Enviroment.Objective_Function(i) + "=[];" ;
        eval(gen_obj_function);
        clearvars gen_obj_function
    end
end


empty_Population.Cost = [];
empty_Population.Pbest.Position = [];
empty_Population.Pbest.Cost = [];

Population = repmat(empty_Population, Optimization_Enviroment.nPop, 1);
clearvars empty_Population
%% GlobalBest Create

GlobalBest.Position = [];
GlobalBest.Cost = inf;
%% Create Random Population Members

for i = 1:Optimization_Enviroment.nPop
    
    % Create Random Position
    Population(i).Position = unifrnd(Optimization_Enviroment.Var_Min, Optimization_Enviroment.Var_Max, Optimization_Enviroment.VarSize);
    
    % Position Round
    Population(i).Position = round(Population(i).Position,2);
    
    % Zero Velocity
    Population(i).Velocity = zeros(Optimization_Enviroment.VarSize);
    
end


if Optimization_Enviroment.Cost_Function == "MotorCad"
    % Input Variables
    for i = 1:Optimization_Enviroment.nPop
        Input_Variables(i,:) = Population(i).Position;
    end
  
    motorCadAnalysisData =motorCadAnalysis(Optimization_Enviroment,Input_Variables);
    Population = postDatatoPopulsation(motorCadAnalysisData, Population, Optimization_Enviroment);

end

if Optimization_Enviroment.Cost_Function == "JMAG"
    % Input Variables
    for i = 1:Optimization_Enviroment.nPop
        Input_Variables(i,:) = Population(i).Position;
    end
  
    % JMAG Analysis
    addpath('Jmag_Analysis\');
    JMAG_Analysis_Data = JMAG_Analysis(Optimization_Enviroment, Input_Variables);
    % Read Data
    Population = JMAG_Read_Data(JMAG_Analysis_Data, Population, Optimization_Enviroment);

end



