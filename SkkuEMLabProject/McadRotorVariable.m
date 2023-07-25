function variable = McadRotorVariable(fileName)
    variable = struct(); 
    variable.motFile=fileName;
        %Axial
    variable.Motor_Length              =[]   ;       
    variable.Rotor_Lam_Length          =[]   ;                   % Rotor lamination pack length
    variable.Magnet_Length             =[]   ;                   % Magnet length

    

    %% Absolute 
    variable.BPMRotor                             =[];

    variable.VMagnet_Layers         =[];      
      
    variable.MagnetThickness_Array = [];    
    variable.BridgeThickness_Array = [];    
    variable.PoleVAngle_Array = [];
    variable.VShapeMagnetPost_Array = [];       
    variable.MagnetSeparation_Array = [];
    

    % Ratio (Interior V(Web) BPMRotor =11

    % Banding Thickness
    variable.Banding_Thickness        =[];                      % [mm]
    % Shaft             
    variable.Shaft_Dia_Front           =[];
    variable.Shaft_Dia_Rear            =[];
    variable.Shaft_Dia                 =[];
    variable.Shaft_Hole_Diameter       =[];    

    % Ratio
    variable.Ratio_BandingThickness    =[];                                             % [mm]
    variable.Ratio_ShaftD              =[];    
    variable.Ratio_ShaftHole           =[];      
    
    variable.RatioArray_PoleArc = [];              % p.u    
    variable.RatioArray_WebThickness = [];         % p.u           
    variable.RatioArray_VWebBarWidth = [];         % p.u           
    variable.RatioArray_WebLength = [];            % p.u   


    %%  Ratio (Interior U(Web) BPMRotor =10
    variable.Magnet_Layers              =[];
end