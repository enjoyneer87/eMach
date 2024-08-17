%% Inverted Delta with - Interior V web Templete
% 

mcad = actxserver('MotorCAD.AppAutomation');


[success,VShapeMagnetClearance_Array] = invoke(mcad,'GetVariable','VShapeMagnetClearance_Array');

% Geometry 


% Get value


%
[success,p_Pole_Pair] = invoke(mcad,'GetVariable','Pole_Number');
p_Pole_Pair=p_Pole_Pair/2;                                                              %     mcApp.SetVariable('Pole_Number', 2*p_Pole_Pair)                            # Rotor poles
[success,p_Stator_Slots] = invoke(mcad,'GetVariable','Slot_Number');                    %     mcApp.SetVariable('Slot_Number', p_Stator_Slots)                           # Stator slots
[success,p_Tooth_Tip_Depth    ] = invoke(mcad,'GetVariable','Tooth_Tip_Depth');         %     mcApp.SetVariable('Tooth_Tip_Depth', p_Tooth_Tip_Depth)                    # Tooth tip depth
[success,p_Tooth_Tip_Angle    ] = invoke(mcad,'GetVariable','Tooth_Tip_Angle');         %     mcApp.SetVariable('Tooth_Tip_Angle', p_Tooth_Tip_Angle)                    # Tooth tip angle
% [success,p_Stator_OD           ] = invoke(mcad,'GetVariable','Stator_Lam_Dia');        %      mcApp.SetVariable('Stator_Lam_Dia', p_Stator_OD)                           # Stator OD
[success,p_Wdg_Overhang   ]=invoke(mcad,'GetVariable','EWdg_Overhang_[R]'      );      %     mcApp.SetVariable('EWdg_Overhang_[R]', p_Wdg_Overhang)                     # End winding overhang (rear)
[success,p_Wdg_Overhang   ]=invoke(mcad,'GetVariable','EWdg_Overhang_[F]'      );      %     mcApp.SetVariable('EWdg_Overhang_[F]', p_Wdg_Overhang)                     #                      (front)
[success,p_Airgap_Mecha       ] = invoke(mcad,'GetVariable','Airgap');                  %     mcApp.SetVariable('Airgap', p_Airgap_Mecha)                                # Mechanical airgap
[success,p_Shaft_OD_Ratio  ]=invoke(mcad,'GetVariable',"Ratio_ShaftD"           );      %     mcApp.SetVariable("Ratio_ShaftD", p_Shaft_OD_Ratio)                        # Shaft OD ratio
[success,p_Mag_Separation_Min]=invoke(mcad,'GetVariable','MinMagnetSeparation'    );    %     mcApp.SetVariable('MinVMagnetAspectRatio', p_Mag_AspectRatio_Min)          # Minimum magnet aspect ratio
[success,p_Shaft_Separation_Min]=invoke(mcad,'GetVariable','MinShaftSeparation'     );  %     mcApp.SetVariable('MinShaftSeparation', p_Shaft_Separation_Min)            # Minimum separation between shaft and magnets
[success,p_Mag_AspectRatio_Min]=invoke(mcad,'GetVariable','MinVMagnetAspectRatio'  );    %    mcApp.SetVariable('MinMagnetSeparation', p_Mag_Separation_Min)             # Minimum separation between magnet poles  
[success,p_Mag_Width_Ratio]=invoke(mcad,'GetVariable','RatioArray_MagnetBarWidth'  );    %    mcApp.SetArrayVariable("RatioArray_MagnetBarWidth", 0, p_Mag_Width_Ratio)  # Magnet width ratio
[success,p_Mag_Clear]=invoke(mcad,'GetVariable','VShapeMagnetClearance_Array'  );       %     mcApp.SetArrayVariable("VShapeMagnetClearance_Array", 0, p_Mag_Clear)      # Magnet clearance
%% Ratio Hierachy 
% 
% 
% 
% 
% 
% 
% 

% stator
[success,i_Stator_OD           ] = invoke(mcad,'GetVariable','Stator_Lam_Dia');        %      mcApp.SetVariable('Stator_Lam_Dia', i_Stator_OD)                           # Stator OD

[success,i_Split_Ratio]=invoke(mcad,'GetVariable','Ratio_Bore' );
        [success,i_MinBackIronThickness]=invoke(mcad,'GetVariable','MinBackIronThickness' );
[success,p_Slot_Depth_Ratio]=invoke(mcad,'GetVariable',"Ratio_SlotDepth_ParallelTooth" );
[success,i_Tooth_Width_Ratio]=invoke(mcad,'GetVariable',"Ratio_ToothWidth" );
[success,i_Slot_Op_Ratio]=invoke(mcad,'GetVariable',"Ratio_SlotOpening_ParallelTooth" );

[success,i_Tooth_Width]=invoke(mcad,'GetVariable',"Tooth_Width" );
% Stator
i_Split_Ratio       %Ratio of stator bore
i_MinBackIronThickness % to be user-defined with Y to T ratio
p_Slot_Depth_Ratio  %"Ratio_SlotDepth_ParallelTooth" );  %% Fixed
i_Tooth_Width_Ratio %"Ratio_ToothWidth" );
i_Slot_Op_Ratio     %"Ratio_SlotOpening_ParallelTooth" );

u_YtoT

i_MinBackIronThickness=u_YtoT*i_Tooth_Width;;
% Set Variable
invoke(mcad,'SetVariable','MinBackIronThickness',i_MinBackIronThickness);
i_MinBackIronThickness

% Input
% 

[success,i_Mag_Thick] = invoke(mcad,'GetVariable','MagnetThickness_Array'); %# Magnet thickness
invoke(mcad,'SetVariable','MagnetThickness_Array',i_Mag_Thick);


% Notch_Depth=0;
Magnet_Layers=2;

%% Layer 1 - insider
L1_Magnet_Thickness     =5.2;
L1_Bridge_Thickness     =1.8;
L1_Pole_V_angle         =112;
L1_Magnet_Post          =1.5;
L1_Magnet_Separation       =6.2;
L1_Magnet_Segments      =1;
% L1 Mag Gap Inner
% L1 Mag Gap Outer

%% Layer 2
L2_Magnet_Thickness  =5.8;
L2_Bridge_Thickness  =1.5;
% L2_Pole_V_angle      =180;
%% 
% 

 % Fixed parameters

p_Pole_Pair           
p_Stator_Slots        
p_Tooth_Tip_Depth    
p_Tooth_Tip_Angle    
% p_Stator_OD           
p_EndSpace_Height     
p_Wdg_Overhang        
p_Airgap_Mecha       
p_Mag_Clear          
p_Shaft_OD_Ratio      
p_Mag_Width_Ratio     
p_Mag_Separation_Min  
p_Shaft_Separation_Min
p_Mag_AspectRatio_Min 

% Absolute variables ??
i_Active_Length     %Active length
i_Mag_Thick         %Magnet thickness
i_Mag_Post          %Magnet post
i_Pole_V_Angle      %V-angle in mech. degrees
i_Tooth_Width_Ratio %Ratio of tooth width
p_Slot_Depth_Ratio  %Ratio of slot depth
i_Slot_Op_Ratio     %Ratio of slot opening
i_Pole_Arc_Ratio    %Ratio of pole arc or magnet V width

%user variable
u_Bridge_Thickness
u_UShape_BridgeThickness_Array
u_BridgeThickness_Array

% user ratio
i_Bridge_thickness_Ratio
i_aspect_ratio

%% 
% All ratios

% User Ratio
u_BridgeThickness_Array;
i_Bridge_Thick;      %Bridge thickness
i_Bridge_thickness_Ratio=u_Bridge_Thickness/u_RotorDiameter;
i_aspect_ratio=i_Active_Length/i_Stator_OD; % x<0.5 may result in mechanical problems x [ 0.5, 1] most efficient x ~1 power-dense, low intertial, X>2 rotor mechanical problems

[success,u_RotorDiameter            ]=invoke(mcad,'GetVariable',"RotorDiameter");
[success,u_Bridge_Thickness            ]=invoke(mcad,'GetVariable',"Bridge_Thickness");    
[success,u_UShape_BridgeThickness_Array            ]=invoke(mcad,'GetVariable',"UShape_BridgeThickness_Array");    
[success,u_BridgeThickness_Array            ]=invoke(mcad,'GetVariable',"BridgeThickness_Array");   

% ex, Weight_Act         = mcApp.GetVariable("Weight_Calc_Total")        # Active mass
%  mcApp.SetVariable('Stator_Lam_Dia', i_Stator_OD)

% Rotor
RatioArray_UMagnetWebThickness  %'RatioArray_UMagnetWebThickness');
RatioArray_UMagnetDiameter      %'RatioArray_UMagnetDiameter');
RatioArray_UMagnetOuterLength   %'RatioArray_UMagnetOuterLength');
RatioArray_UMagnetOuterOffset   %'RatioArray_UMagnetOuterOffset');
% Shaft
[success,RatioArray_UMagnetWebThickness]=invoke(mcad,'GetVariable','RatioArray_UMagnetWebThickness');
[success,RatioArray_UMagnetDiameter]=invoke(mcad,'GetVariable','RatioArray_UMagnetDiameter');
[success,RatioArray_UMagnetOuterLength]=invoke(mcad,'GetVariable','RatioArray_UMagnetOuterLength');
[success,RatioArray_UMagnetOuterOffset]=invoke(mcad,'GetVariable','RatioArray_UMagnetOuterOffset');

"GeometryParameterisation"
"Ratio_Bore"
"Ratio_SlotDepth_ParallelTooth"
"Ratio_SlotDepth_ParallelSlot"
"Ratio_SlotWidth"
"Ratio_SlotOpening_ParallelSlot"
"Ratio_SlotOpening_ParallelTooth"
"Ratio_ToothTip"
"Ratio_ToothWidth"
"Ratio_SleeveThickness"
"Ratio_RotorD"
"Ratio_BandingThickness"
"Ratio_ShaftD"
"Ratio_ShaftHole"
"Ratio_MagnetThickness"
"Ratio_MagnetArc"
"Ratio_MagnetReduction"
"Ratio_BarT_Depth"
"Ratio_BarT_Opening_Depth"
"Ratio_BarT_Opening_Depth_Round"
"Ratio_Rotor_Tooth_Width_T"
"Ratio_BarT_Width_Round"
"Ratio_BarT_Width_Rectangular"
"Ratio_BarT_Opening_ParallelTooth"
"Ratio_BarT_Opening_Round"
"Ratio_BarT_Opening_Rectangular"
"Ratio_BarT_Opening_PearCircular"
"Ratio_BarT_Corner_Radius_Pear"
"Ratio_BarT_Corner_Radius_ParallelTooth"
"Ratio_BarT_Corner_Radius_PearCircular"
"Ratio_BarT_Opening_Radius"
"Ratio_BarT_Opening_Radius_PearCircular"
"Ratio_BarT_Tip_Angle"
"Ratio_BarB_Tip_Angle"
"Ratio_BarB_Depth"
"Ratio_BarB_Opening_Depth"
"Ratio_BarB_Opening_Depth_Round"
"Ratio_Rotor_Tooth_Width_B"
"Ratio_BarB_Width_Round"
"Ratio_BarB_Width_Rectangular"
"Ratio_BarB_Opening_ParallelTooth"
"Ratio_BarB_Opening_Round"
"Ratio_BarB_Opening_Rectangular"
"Ratio_BarB_Opening_PearCircular"
"Ratio_BarB_Corner_Radius_Pear"
"Ratio_BarB_Corner_Radius_ParallelTooth"
"Ratio_BarB_Corner_Radius_PearCircular"
"Ratio_BarB_Opening_Radius"
"Ratio_BarB_Opening_Radius_PearCircular"
"RatioArray_MagnetBarWidth"
"RatioArray_MagnetVWidth"
"RatioArray_MagnetShift"
"RatioArray_WebLength"
"RatioArray_VWebBarWidth"
"RatioArray_WebThickness"
"RatioArray_PoleArc"
"RatioArray_UMagnetOuterOffset"
"RatioArray_UMagnetInnerOffset"
"RatioArray_UMagnetOuterLength"
"RatioArray_UMagnetInnerLength"
"RatioArray_UMagnetDiameter"
"RatioArray_UMagnetWebThickness"
%% python
% python - ?dd

[success,i_Mag_Thick                  ]=invoke(mcad,'GetVariable',"RotorDiameter");
[success,u_RotorDiameter              ]=invoke(mcad,'GetVariable',"RotorDiameter");


    mcApp.SetVariable('MinVMagnetAspectRatio', p_Mag_AspectRatio_Min)          %# Minimum magnet aspect ratio
    mcApp.SetVariable('MinMagnetSeparation', p_Mag_Separation_Min)             %# Minimum separation between magnet poles  
    mcApp.SetVariable('MinShaftSeparation', p_Shaft_Separation_Min)            %# Minimum separation between shaft and magnets
    mcApp.SetVariable("Ratio_ShaftD", p_Shaft_OD_Ratio)                        %# Shaft OD ratio

    mcApp.SetArrayVariable("RatioArray_MagnetBarWidth", 0, p_Mag_Width_Ratio)  %# Magnet width ratio
    mcApp.SetArrayVariable("VShapeMagnetClearance_Array", 0, p_Mag_Clear)      %# Magnet clearance

    mcApp.SetVariable('Ratio_Bore', i_Split_Ratio)                             %# Split ratio
    mcApp.SetVariable('Ratio_ToothWidth', i_Tooth_Width_Ratio)                 %# Tooth width ratio

    mcApp.SetVariable('Ratio_SlotDepth_ParallelTooth', p_Slot_Depth_Ratio)     %# Slot depth ratio
    mcApp.SetVariable('Ratio_SlotOpening_ParallelTooth', i_Slot_Op_Ratio)      %# Slot opening width ratio 

    mcApp.SetArrayVariable("RatioArray_MagnetVWidth", 0, i_Pole_Arc_Ratio)     %# Pole arc ratio
    mcApp.SetArrayVariable('BridgeThickness_Array', 0, i_Bridge_Thick)         %# Bridge thickness 
    mcApp.SetArrayVariable("MagnetThickness_Array", 0, i_Mag_Thick)            %# Magnet thickness
    mcApp.SetArrayVariable("PoleVAngle_Array", 0, i_Pole_V_Angle)              %# V-shape layer angle
    mcApp.SetArrayVariable("VSimpleMagnetPost_Array", 0, i_Mag_Post)           %# Magnet post  
    mcApp.SetArrayVariable("VSimpleEndRegion_Outer_Array", 0, Air_Pocket)      %# Air pocket extensions (outer)
    mcApp.SetArrayVariable("VSimpleEndRegion_Inner_Array", 0, Air_Pocket)      %#                       (inner)
   

% Winding   

 
% |### get Assign winding parameters|

[success,p_Coils_Slot   ] = invoke(mcad,'GetVariable','WindingLayers');
[success,p_Turns_Coil   ] = invoke(mcad,'GetVariable','MagTurnsConductor');
[success,p_Parallel_Path] = invoke(mcad,'GetVariable','ParallelPaths');
[success,p_Slot_Fill    ] = invoke(mcad,'GetVariable','RequestedGrossSlotFillFactor');

p_Coils_Slot   
p_Turns_Coil   
p_Parallel_Path
p_Slot_Fill
%% 
% ### Materials

p_Yield_Rotor  = 460.   # Rotor core yield strength
p_Temp_Wdg_Max = 180.   # Maximum winding temperature
p_Temp_Mag_Max = 140.   # Maximum magnet temperature
%% 
% ### Performance

p_Speed_Max        = 7000.   # Maximum operating speed
p_Line_Current_RMS = 500.    # Maximum RMS line current
%% 
% ### Calculation settings

p_Speed_Lab_Step    = 100.                              # Speed step used in Lab
p_Speed_Peak_Array  = np.array([500., 3000., 6000.])    # Speeds for peak performance calculation 
p_Speed_Cont_Array  = np.array([1000., 5000.])          # Speeds for continuous performance calculation
p_Torque_Pts        = 90                                # Timesteps per cycle for torque calculation
%% 
% ### Post-processing

Pic_Export = 1      # Export geometry snapshots (0: No; 1: Yes)
%% 
% ### Dependent parameters

Speed_Max_Rad = pi*p_Speed_Max/30                                               # Maximum speed in radians
Speed_Lab     = np.arange(0, p_Speed_Max + p_Speed_Lab_Step, p_Speed_Lab_Step)  # Speed vector in Lab
Speed_Lab     = Speed_Lab.tolist()                                              # Required for signal generation
Speed_Lab_Len = len(Speed_Lab)                                                  # Required for signal generation
%% 
% ### Input parameters for testing in IDE or initialisation in OSL Python node

% if run_mode in ['OSL_setup', 'IDE_run']:
% 
%     i_Active_Length     = 110.   # Active length
% %   i_Mag_Thick         = 5.5    # Magnet thickness
%     i_Mag_Post          = 2.0    # Magnet post
%     i_Bridge_Thick      = 1.0    # Bridge thickness
%     i_Pole_V_Angle      = 110.   # V-angle in mech. degrees
%     i_Split_Ratio       = 0.6    # Ratio of stator bore
%     i_Tooth_Width_Ratio = 0.5    # Ratio of tooth width
%     p_Slot_Depth_Ratio  = 1   # Ratio of slot depth
%     i_Slot_Op_Ratio     = 0.7    # Ratio of slot opening
%     i_Pole_Arc_Ratio    = 0.8    # Ratio of pole arc or magnet V width

[success,Machine_Length    ]=invoke(mcad,'GetVariable','Motor_Length'           );
[success,i_Active_Length  ]=invoke(mcad,'GetVariable','Stator_Lam_Length'      );
[success,i_Active_Length   ]=invoke(mcad,'GetVariable','Rotor_Lam_Length'       );
[success,i_Active_Length   ]=invoke(mcad,'GetVariable','Magnet_Length'          );
% |Lab: continuous performance|


%   # Settings
    mcApp.SetVariable("LabThermalCoupling", 1)                         # Coupling with Thermal
    mcApp.SetVariable("OpPointSpec_MotorLAB", 2)                       # Max temperature definition
    mcApp.SetVariable("StatorTempDemand_Lab", p_Temp_Wdg_Max)          # Max winding temperature
    mcApp.SetVariable("RotorTempDemand_Lab", p_Temp_Mag_Max)           # Max magnet temperature
    mcApp.SetVariable("ThermMaxCurrentLim_MotorLAB", 0)                # Useful?
    mcApp.SetVariable("Iest_MotorLAB", p_Line_Current_RMS*sqrt(2)*0.3) # Initial line current (rms)
    mcApp.SetVariable("Iest_RMS_MotorLAB", p_Line_Current_RMS*0.3)     # Initial line current (peak)
%% 
% Input

    d
%% 
% P

    p_Mag_Width_Ratio
%% 
% O