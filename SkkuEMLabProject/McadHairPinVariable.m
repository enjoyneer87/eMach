function variable= McadHairPinVariable(fileName)
    variable                                         =struct();  
    variable.motFile                                 =fileName ;
    %% Input>Winding
    %>> pattern
    % Design - left
    % Winding Type
    variable.Input.MagneticWindingTypeHairpin       =1;
    % variable.MagneticWindingType                  =1;
    % Winding Type Method (right Below)         
    variable.Input.HairpinWindingPatternMethod       =1;
    % Design  - right                              
    variable.Input.MagThrow                         =[];                 % 권선 피치
    variable.Input.WindingLayers                    =[];                 % 슬롯 내 턴 수
    variable.Input.ParallelPaths_Hairpin            =[];                 % 병렬 수
    % variable.ConductorsPerSlot                                         % WindingLayers 에 따라 자동으로 적용됨
                                   
                                    
    %% >> Definition                                
    variable.Input.Armature_CoilStyle               =1;                  % Coil Style : Hairpin
    variable.Input.Winding_Type                     =[];                 % Overlapping or non-overlapping winding
    % variable.Input.Armature_Winding_Definition    =[];                 % The winding can be defined by the copper slot fill, wire size, or heavy build slot fill
    variable.Input.Wedge_Model                      =[];                 % Wedge Model 0 = Non_Conductive, 1 = Wound_Space, 2 = Conductive, 3 = Air
    % wire Selection                               
    variable.Input.Copper_Width                     =[];            
    variable.Input.Copper_Height                    =[];     
    variable.Input.Insulation_Thickness             =[];                 % 도체 절연체 두께                                    
    variable.Input.Copper_Corner_Radius             =[];             
    variable.Input.Copper_Corner_Radius_2           =[];             
    variable.Input.Copper_Corner_Radius_3           =[];             
    %  Box - Input Parameter                           
    variable.Input.Liner_Thickness                  =[];                 % 절연지 두께
    variable.Input.Copper_Depth_percent             =[];             
    variable.Input.ConductorSeparation              =[];                 % 방사방향 도체 사이 거리
    variable.Input.NumberOfWireSizes                =[];         
    %% Output -left
    % Wire_Slot_Fill_(Wdg_Area)
    % EWdg_Fill                               % but Output Wire fill factor for armature end-winding, i.e. total wire volume/end-winding volume
    % Conductors_Slot_IM1PH
    % EWdg_MLT
    % ArmatureEWdgMLT_Calculated
    %% backup
    % FirstSetConductors - 
    % TotalConductors    - setting
    
    % Output - right
    variable.Output.NoMushConductorsDrawn           =[];                % Conductors/Slot Drawn                        o/p WindingDesign   This number of conductors drawn for mush winding (this may not be the number of conductors specified)              
    variable.Output.Wire_Slot_Fill_Wdg_Area         =[];                % Wire Slot Fill(Wdg Area)                     o/p winding                        
    % Wire_Slot_Fill_(Wdg_Area)
    variable.Output.Slot_Fill_Slot_Area             =[];                % Wire Slot Fill(SLot Area)                    o/p winding                                                               
    % Slot_Fill_(Slot_Area)
    variable.Output.GrossSlotFillFactor             =[];                % Copper Slot Fill (Slot Area)                 o/p winding   The gross slot fill of copper in slot (copper area/slot area)                                    
    variable.Output.NetSlotFillFactor               =[];                %  Heavy Build Slot Fill                       o/p winding                 The net slot fill of wire in slot (Heavy build)                                          
    variable.Output.Area_Slot                       =[];                %  Slot Area                          [mm2]    o/p Dimension                Slot area - including liner and wedge but not slot opening
    variable.Output.Area_Slot_NoWedge               =[];                %                                     [mm2]    o/p Dimension Slot area - including liner but not slot opening or wedge
    variable.Output.Area_Winding_With_Liner         =[];                %  Winding Area(+Liner)               [mm2]    o/p Dimension  Slot area available for winding before liner insertion                                          
    variable.Output.Area_Winding_No_Liner           =[];                %  Winding Area                       [mm2]    o/p Dimension   Slot area available for winding after liner insertion       
    variable.Output.Winding_Depth                   =[];                %  Winding Depth                      [mm]     o/p winding
    variable.Output.Area_Covered_Wire               =[];                %  Covered Wire Area                  [mm2]    o/p winding  Area of wire in the slot (includes wire insulation)
    variable.Output.Area_Covered_Wire_Total         =[];                %  Covered Wire Area                  [mm2]    o/p winding  Total area of wire in the slot (includes wire insulation)    
    variable.Output.Covered_Wire_Area               =[];                %  Covered Wire Area                  [mm2]  
    variable.Output.Area_Copper                     =[];                %  Copper Area                        [mm2]    o/p winding Area of wire conductor in the slot (not including insulation) 
    variable.Output.Area_Copper_Total               =[];                %  Copper Area                        [mm2]    o/p winding Total area of conductor in the slot (not including insulation)         
    variable.Output.Copper_Area                     =[];                %  Copper Area                        [mm2]    o/p winding
    variable.Output.Area_Impreg_No_Liner_Lam        =[];                %  Impreg Area                        [mm2]    o/p Dimension          Impregnation area/slot - not including gap between liner and lamination        
    variable.Output.LitzImpregArea                  =[];                %  Impreg Area                        [mm2]    o/p WindingDesign      Area of impregnation within litz bundles
    variable.Output.Area_SlotWedge                  =[];                %  Wedge Area                         [mm2]    op/ Dimension         Slot wedge area/slot (includes slot area used to force conductors to base of slot)
                               
end