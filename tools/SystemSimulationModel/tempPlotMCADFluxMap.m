function tempPlotMCADFluxMap(MotorCADFEA)

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
    figure(1);
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
    
    figure(2);
    hold on
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
    figure(3);
    hold on
    mesh(id_new,iq_new,lambda_d_new);
    xlabel('I_d [A]')
    ylabel('I_q [A]')
    title('\lambda_d_{Interp}'); grid on;
    figure(4);
    hold on
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
end 