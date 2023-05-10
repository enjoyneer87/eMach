
% Environment Setting- Optmization Method Selection 
% Cost_Function
% Test Function
% Alogorithm
    % Particle Swarm Optimzation (PSO) Algorithm
    % ePSO Mads
    % Multi-Objective Particle Swarm Optimization (MOPSO) Algorithm
    % Non-Dominated Sorting Genetic Algorithm II (NSGA II) Algorithm
% Variable Setting
% Objective Function Setting
% Weighted Sum for Single-Objective Optimization
% Operation of Optimization


%% Environment Setting
Optimization_Enviroment.Optimization_Method = "PSO"; % Optmization Method Selection

% Cost_Function

Optimization_Enviroment.Cost_Function = "MotorCad";  %Cost Function
Optimization_Enviroment.FileName = HDEV1motorcad.file_name;

Optimization_Enviroment.FileName = '12P72S_N42EH_Br_95pro_11T_Fidelity_study'
Optimization_Enviroment.motorCad.current_path ='Z:\Thesis\HDEV\02_MotorCAD\backup\'


%% Particle Swarm Optimzation (PSO) Algorithm

if Optimization_Enviroment.Optimization_Method == "PSO"

    Optimization_Enviroment.Maxit = 100 ;
    Optimization_Enviroment.w = 1 ;
    
    Optimization_Enviroment.c1 = 2 ;
    Optimization_Enviroment.c2 = 2 ;    
    Optimization_Enviroment.wdamp = 0.9 ;
    Optimization_Enviroment.nPop = 30 ;
    
end

%% ePSO Mads

if Optimization_Enviroment.Optimization_Method == "ePSO+MADS"

    % ePSO setting
    Optimization_Enviroment.Maxit = 100 ;
    Optimization_Enviroment.nPop = 15 ;
    
    Optimization_Enviroment.w = 1 ;
    Optimization_Enviroment.wdamp = 0.8 ;
    
    Optimization_Enviroment.c1 = 2 ;
    Optimization_Enviroment.c2 = 2 ;

    Optimization_Enviroment.max_cluster = 20 ;
    
    % mads setting
    Optimization_Enviroment.mads.inital_mesh_size = 1 ;
    Optimization_Enviroment.mads.mesh_size_ratio = 0.1 ;
    Optimization_Enviroment.mads.tau = 4;
    Optimization_Enviroment.mads.wm = -1;
    Optimization_Enviroment.mads.wp = 1;
    
end

%% Variable Setting

if Optimization_Enviroment.Cost_Function == "JMAG"
    
    Optimization_Enviroment.Var_Name =   ["C_R" "C_X" "M1_A" ]';

                                        %  C_R X M1_A 
    Optimization_Enviroment.Var_Min   =   [10  4 115  ];
    Optimization_Enviroment.Var_Base  =   [12  5 130  ];
    Optimization_Enviroment.Var_Max   =   [14  6 150  ];
    Optimization_Enviroment.Var_order =   floor(0:length(Optimization_Enviroment.Var_Base)-1);     
    
    Optimization_Enviroment.nVar = size(Optimization_Enviroment.Var_order,2);
    Optimization_Enviroment.VarSize = [1 Optimization_Enviroment.nVar];


%% Objective Function Setting
Optimization_Enviroment.JMAG.ModelName = ["Electromagnetics"];
Optimization_Enviroment.JMAG.StudyName = ["Torque" "BackEMF"];
Optimization_Enviroment.Objective_Function = ["EuclidianNorm"  ];

% Multi-Objective Optimization Setting
% Optimization_Enviroment.Definition_Problem_Maximize = ["Torque" "TorqueRipple"]; 
% Optimization_Enviroment.Definition_Problem_Minimize = ["BackEMF"]; 

% Example (order) 
% Optimization_Enviroment.JMAG.ModelName = ["Electromagnetics" "Structure"];
% Optimization_Enviroment.JMAG.StudyName = ["Torque" "BackEMF" "CoggingTorque" "Stress"];
% Optimization_Enviroment.Objective_Function = ["Torque" "TorqueRipple"  "Saliency_Ratio" "CoggingTorque" "BackEMF_THD" "Stress"]

end

%% Weighted Sum for Single-Objective Optimization
if Optimization_Enviroment.Optimization_Method == "PSO" || Optimization_Enviroment.Optimization_Method == "ePSO+MADS"

% f1 : Torque
% f2 : TorqueRipple
% f3 : Stress
% f4 : BackEMF THD
% f5 : CoggingTorque
% Minimize

%     Optimization_Enviroment.Weight_SUM = @(f1,f2,f3) (1/f1 + f2 + f3);
    Optimization_Enviroment.Weight_SUM = @(f1) (f1);

end

%% Operation of Optimization

if Optimization_Enviroment.Optimization_Method == "PSO"
    
    addpath('PSO\');
    [Total_Population, Total_GlobalBest] = PSO_Algorithm(Optimization_Enviroment);
    
end
