classdef motorCadGeometryRotor
    properties
    %% Absolute 

        MagnetThickness_Array
        BridgeThickness_Array
        PoleVAngle_Array
        VShapeMagnetPost_Array
        MagnetSeparation_Array
        MagnetSegments_Array

    %% Ratio (Interior V(Web) BPMRotor =11
        RatioArray_PoleArc
        RatioArray_WebThickness
        RatioArray_VWebBarWidth
        RatioArray_WebLength
    end
    
    methods
        function obj = motorCadGeometryRotor(tbl)
            tbl = replaceSpacesWithUnderscores(tbl);
    %% Absolute 
     
            obj.MagnetThickness_Array = [tbl.L1_Magnet_Thickness, tbl.L2_Magnet_Thickness];
            % obj.BridgeThickness_Array = [tbl.L1_Bridge_Thickness, tbl.L2_Bridge_Thickness];
            obj.PoleVAngle_Array = [tbl.L1_Pole_V_Angle, tbl.L2_Pole_V_Angle];
            % obj.VShapeMagnetPost_Array = [tbl.L1_Magnet_Post, tbl.L2_Magnet_Post];
            obj.MagnetSeparation_Array = [tbl.L1_Magnet_Separation, tbl.L2_Magnet_Separation];
            % obj.MagnetSegments_Array = [tbl.L1_Magnet_Segments, tbl.L2_Magnet_Segments];
            
    %% Ratio (Interior V(Web) BPMRotor =11
            obj.RatioArray_PoleArc = [tbl.L1_Pole_Arc, tbl.L2_Pole_Arc];
            obj.RatioArray_WebThickness = [tbl.L1_Web_Thickness, tbl.L2_Web_Thickness];
            obj.RatioArray_VWebBarWidth = [tbl.L1_Magnet_Bar_Width, tbl.L2_Magnet_Bar_Width];
            obj.RatioArray_WebLength = [tbl.L1_Web_Length, tbl.L2_Web_Length];
        end
    end
end
