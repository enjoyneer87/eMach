%% Create Lookup Tables From Flux Data
%
% Using MathWorks tools, you can create lookup tables for an interior
% permanent magnet synchronous motor (PMSM) that characterizes the d-axis
% and q-axis current as a function of d-axis and q-axis flux.
% |CreatingIdIqTable| calls |gridfit| to model the current surface from
% scattered or semi-scattered flux data.

% Copyright 2017-2018 The MathWorks, Inc.
%% Step 1: Load and Preprocess Data
%
% Load the data from a |mat| file captured from a dynamometer or 
% another CAE tool.
% load FEAdata.mat
% MotorCADFEA=load('Z:\01_Codes_Projects\git_fork_emach\tools\SystemSimulationModel\DOE\Plaid_A2B2_DegC_20\Lab\SatuMap.mat');
SatuMapMatPath='Z:\01_Codes_Projects\git_fork_emach\tools\SystemSimulationModel\DOE\Plaid_A2B2_DegC_20\Lab\SatuMap.mat'
MotorCADFEA=load(SatuMapMatPath);


FEAdata.flux.d            =  MotorCADFEA.Flux_Linkage_D';
FEAdata.flux.q            =  MotorCADFEA.Flux_Linkage_Q';
FEAdata.current.d         =  MotorCADFEA.Id_Peak(:,1)'  ;    
FEAdata.current.q         =  MotorCADFEA.Iq_Peak(1,:)   ;    
CurrentTableEdge=max(abs(FEAdata.current.d));

% Determine the minimum and maximum flux values
flux_d_min = min(min(FEAdata.flux.d)) ;
flux_d_max = max(max(FEAdata.flux.d)) ;
flux_q_min = min(min(FEAdata.flux.q)) ;
flux_q_max = max(max(FEAdata.flux.q)) ;

% Plot the sweeping current points used to collect the data
for i = 1:length(FEAdata.current.d)
    for j = 1:1:length(FEAdata.current.q)
    plot(FEAdata.current.d(i),FEAdata.current.q(j),'b*');
    hold on
    end
end


% scatter(id_matrix,iq_matrix,'k');


% Plot the current limit circle
for angle_theta = pi/2:(pi/2/200):(3*pi/2)
    plot(CurrentTableEdge*cos(angle_theta),CurrentTableEdge*sin(angle_theta),'r.');
    hold on
end
xlabel('I_d [A]')
ylabel('I_q [A]')
title('Sweeping Points'); grid on;
xlim([-CurrentTableEdge,0]);
ylim([-CurrentTableEdge,CurrentTableEdge]);
hold off

% scatter(Id,Iq)


%% Step 2: Generate Evenly Spaced Table Data From Scattered Data
%
% The flux tables flux_d and flux_q can have different step sizes for id
% and iq because id is primarily dependent on d-axis flux and iq is
% primarily dependent on q-axis flux.  Evenly spacing the rows and columns
% helps improve interpolation accuracy.

% Set the spacing for the table rows and columns
flux_d_size = 50;
flux_q_size = 50;

% Generate linear spaced vectors for the breakpoints
ParamFluxDIndex = linspace(flux_d_min,flux_d_max,flux_d_size);
ParamFluxQIndex = linspace(flux_q_min,flux_q_max,flux_q_size);

% Create 2-D grid coordinates based on the d-axis and q-axis currents 
[id_m,iq_m] = meshgrid(FEAdata.current.d,FEAdata.current.q);

% Create the table for the d-axis current
id_fit = gridfit(FEAdata.flux.d,FEAdata.flux.q,id_m,ParamFluxDIndex,ParamFluxQIndex);
ParamIdLookupTable = id_fit'; 
figure;
surf(ParamFluxDIndex,ParamFluxQIndex,ParamIdLookupTable'); 
xlabel('\lambda_d [v.s]');ylabel('\lambda_q [v.s]');zlabel('id [A]');title('id Table'); grid on;
shading flat;

% Create the table for the q-axis current
iq_fit = gridfit(FEAdata.flux.d,FEAdata.flux.q,iq_m,ParamFluxDIndex,ParamFluxQIndex);
ParamIqLookupTable = iq_fit'; 
figure;
surf(ParamFluxDIndex,ParamFluxQIndex,ParamIqLookupTable');
xlabel('\lambda_d [v.s]');ylabel('\lambda_q [v.s]');zlabel('iq [A]'); title('iq Table'); grid on;
shading flat;

%% Step 3: Set Block Parameters
%
% Set MATLAB workspace variables that you can use for the Flux-Based PMSM
% block parameters.

% Set the breakpoints
flux_d=ParamFluxDIndex;
flux_q=ParamFluxQIndex;

% Set the table data
id=ParamIdLookupTable;
iq=ParamIqLookupTable;
