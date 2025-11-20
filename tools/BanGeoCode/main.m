clc; clear all; close all;

set(0,'DefaultFigureWindowStyle','docked');
set(0,'defaultfigurecolor',[1 1 1]);

warning('off');
%system('TASKKILL -f -im "Motor-CAD_14_1_5.exe"'); %ubij Mcad

%% Geometry visibility and plotting

n_iteration=1;
n_mcad_run=0;
n_succesfull=0;
n_feasible=0;

% Construction point visibility
rotor_construction=true;

% Polyshape visibility
plot_shapes=true;
plot_regions=true;
plot_arcs=true;

% Minimal distance check
DstChk=true;

path=pwd;

%% Draw and check rotor and stator

while 1 % leave this for debugging
    pause(0.25); %for figure refreshing
    clf(gcf);
    
    
    %% Machine Parameters
    
    % Constants
    in.VMagnet_Layers=          2;
    in.Pole_Number=             8;
    in.Shaft_Dia=               75;
    in.Slot_Number=             48;
    in.Stator_Lam_Dia=          230;
    in.Airgap=                  0.71;
    in.Shaft_Hole_Diameter=     0;
    in.Stator_Lam_Length=       [80 400];
    in.FillFactor=              0.7; %GrossFillFactor
    in.WindingLayers=           6; %    
     
    
    in.Split_ratio=Rnd([0.7 0.8],1);
    % Relative variables
    in.Stator_Bore=round(in.Split_ratio*in.Stator_Lam_Dia,1); %needs to be rounded to the 1 decimal , otherwise mCAD will fail
          
    lay=in.VMagnet_Layers;
    
    % Optimization variables, the user has to manually set limits
    
    in.MagnetThickness_Array=           Rnd([2 6],lay);
    in.VSimpleWidth_Array=              [Rnd([10 15],1) Rnd([15 20],1)]; 
    in.VSimpleMagShift_Array=           Rnd([0 0],lay);
    in.MagnetBarWidth_Array=            Rnd([0.5 1],1).*in.VSimpleWidth_Array;
    in.BridgeThickness_Array=           [Rnd([1 2],1) Rnd([10 15],1)];
    in.PoleVAngle_Array=                [Rnd([120 180],1) Rnd([100 150],1)];
    in.VSimpleEndRegion_Outer_Array=    Rnd([1 1],lay);
    in.VSimpleEndRegion_Inner_Array=    Rnd([1 1],lay);
    in.VSimpleMagnetPost_Array=         Rnd([0.1 3],lay);
    in.VShape_Magnet_ClearanceOuter=    Rnd([0 0],lay);
    in.VShape_Magnet_ClearanceInner=    Rnd([0 0],lay);
    in.VSimpleOffsetT_Array=            Rnd([0 0],lay);    
    in.PoleNotchDepth=                  Rnd([1 10],1);
    in.PoleNotchArc_Inner=              Rnd([5 20],1);
    in.PoleNotchArc_Outer=              1.2*in.PoleNotchArc_Inner;
    
    
    %Fillets single
    in.r_10=Rnd([0 1],1);
    in.r_11=Rnd([0 1],1);
    in.r_M=0.2; %magnet fillet
       
    %% Get all rotor shapes and primitives
    run V_simple_geometry
    
    
    %% Check Rotor feasibility
    flag1=check_feasibility(Rotor,tau_pole,DstChk);    
    
    
    if flag1
        title(['\color{blue}',num2str(n_iteration),'   Pass !'],'FontSize',22);
        n_feasible=n_feasible+1;
    else
        title(['\color{red}',num2str(n_iteration),'   Fail !'],'FontSize',22);
    end
    
    table(n_feasible,n_iteration,n_succesfull,n_mcad_run)
    n_iteration=n_iteration+1;
        
    %% clear for next iteration
    clearvars Rotor Stator drw out
    pause(0.25); %for figure refreshing
end



    function [out] = Rnd(in,N)
    
    %in range of random numbers
    %N number of random vector elements
    
    if numel(in)>1
        for i=1:N
            out(i)=(in(2)-in(1)).*rand(1,1) + in(1);
        end
    else
        out=in;
    end
    
    end
