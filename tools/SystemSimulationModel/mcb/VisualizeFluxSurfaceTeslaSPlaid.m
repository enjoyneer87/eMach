%% Generate Feed-Forward Flux Parameters
%
% Using MathWorks tools, you can create lookup tables for an interior
% permanent magnet synchronous motor (PMSM) controller that characterizes 
% the d-axis and q-axis flux as a function of d-axis and q-axis currents.  
% |VisualizeFluxSurface| loads the flux data and calls |interp2| to 
% interpolate the table data using a spline. Spline interpolation increases 
% table and breakpoint resolution.  

% Copyright 2017-2018 The MathWorks, Inc.
%% Step 1: Load and Preprocess Data
%
% Load the data from a |mat| file captured from a dynamometer or 
% another CAE tool.
% load FEAdata.mat;
% MotorCADFEA=load('Z:\Simulation\LabProj2023BenchMarking\TeslaSPlaid\S_Plaid_M_CAD_1335A_LossModelLSCHighFidel\Lab\SaturationLossMapdq.mat');
% MotorCADFEA=load('Z:\Simulation\LabProj2023BenchMarking\TeslaSPlaid\S_Plaid_M_CAD_1335A_LossModelLSCHighFidel\Lab\S_Plaid_1335A_DegC_minus40_SatuMap.mat')
% MotorCADFEA=load('Z:\01_Codes_Projects\git_Motor_System_Model\Mathworks_ref\HDEV_fluxmodel\HDEV_Model2\Lab\SaturationLossMap_HDEV_Model_LabInterpolate30.mat')
% MotorCADFEA=load('Z:\01_Codes_Projects\Testdata_post\Simulation_Comparison\12P72S_N42EH_Maxis_Br_95pro_LScoil_11T_2ndy_TestModel\Lab\SaturationLossMap_lab_idiq.mat')
% MotorCADFEA=load('Z:\Simulation\LabProj2023BenchMarking\TeslaSPlaid\S_Plaid_M_CAD_1335A_LossModelLSCHighFidel\Lab\S_Plaid_1335A_DegC_minus40_SatuMap.mat');
% MotorCADFEA=load('Z:\01_Codes_Projects\git_fork_emach\tools\SystemSimulationModel\DOE\Plaid_A2B2_DegC_20\Lab\SatuMap.mat');

SatuMapMatPath='Z:\01_Codes_Projects\git_fork_emach\tools\SystemSimulationModel\DOE\Plaid_A2B2_DegC_20\Lab\SatuMap.mat'
MotorCADFEA=load(SatuMapMatPath);

% Load the data matrix.
% lambda_d = FEAdata.flux.d;
% lambda_q = FEAdata.flux.q;
% id       = FEAdata.current.d;
% iq       = FEAdata.current.q;
FEAdata.flux.d            =  MotorCADFEA.Flux_Linkage_D;
FEAdata.flux.q            =  MotorCADFEA.Flux_Linkage_Q;

FEAdata.current.d         =  MotorCADFEA.Id_Peak(:,1)'  ;    
FEAdata.current.q         =  MotorCADFEA.Iq_Peak(1,:)   ;    
  
lambda_d = FEAdata.flux.d';
lambda_q = FEAdata.flux.q';
id = FEAdata.current.d;
iq = FEAdata.current.q;
% id = FEAdata.current.d(:,1)';
% iq = FEAdata.current.q(1,:);






%% Step 2: Generate Evenly Spaced Data
%
% The flux tables flux_d and flux_q can have different step sizes for id
% and iq because id is primarily dependent on d-axis flux and iq is
% primarily dependent on q-axis flux. Evenly spacing the rows and columns
% helps improve interpolation accuracy.




%Visualize the flux surface
figure;
mesh(id,iq,lambda_d);
    hold on

xlabel('I_d [A]')
ylabel('I_q [A]')
title('\lambda_d'); grid on;
% Plot the sweeping current points used to collect the data
for i = 1:length(FEAdata.current.d)
    for j = 1:1:length(FEAdata.current.q)
    plot(FEAdata.current.d(i),FEAdata.current.q(j),'b*');
    hold on
    end
end

figure;
mesh(id,iq,lambda_q);
xlabel('I_d [A]')
ylabel('I_q [A]')
title('\lambda_q'); grid on;

% Set the spacing for the table rows and columns 
flux_d_size = 101;
flux_q_size = 101;

% Use spline interpolation to get higher resolution
id_new = linspace(min(id),max(id),flux_d_size);
iq_new = linspace(min(iq),max(iq),flux_q_size);
lambda_d_new = interp2(id',iq,lambda_d,id_new',iq_new,'spline');
lambda_q_new = interp2(id',iq,lambda_q,id_new',iq_new,'spline');


% Ipk_new = interp2(id',iq,MotorCADFEA.Stator_Current_Line_Peak,id_new',iq_new,'spline');
% beta_new = interp2(id',iq,MotorCADFEA.Phase_Advance,id_new',iq_new,'spline');
% scatter(Ipk_new,beta_new)
%Visualize the flux surface
figure;
mesh(id_new,iq_new,lambda_d_new);
xlabel('I_d [A]')
ylabel('I_q [A]')
title('\lambda_d_{Interp}'); grid on;

figure;
mesh(id_new,iq_new,lambda_q_new);
xlabel('I_d [A]')
ylabel('I_q [A]')
title('\lambda_q_{Interp}'); grid on;

%% Step 3: Set Block Parameters
%
% Set MATLAB workspace variables that you can use
% for the Flux-Based PM Controller block parameters.

% Set the breakpoints
id_index=id_new;
iq_index=iq_new;

% Set the table data
lambda_d=lambda_d_new;
lambda_q=lambda_q_new;
