classdef motorCadGeometryRotor
    properties
        % Array
        % Absolute (상수 값)
        MagnetThickness_Array
        BridgeThickness_Array
        PoleVAngle_Array
        VShapeMagnetPost_Array
        MagnetSeparation_Array
        VShapeMagnetSegments_Array
        % Ratio (Interior V(Web) BPMRotor =11 (비율 값)
        RatioArray_PoleArc
        RatioArray_WebThickness
        RatioArray_VWebBarWidth
        RatioArray_WebLength

        % value
        % absolute
        BPMRotor
        PoleNumber_Outer
        VMagnet_Layers
        Banding_Thickness
        Shaft_Dia
        Airgap
        Shaft_Dia_Front
        Shaft_Dia_Rear
        AxialSegments
        % ratio
        Ratio_BandingThickness
        Ratio_ShaftD

    end

    methods
        function obj = motorCadGeometryRotor(InputTable,VMagnet_Layers)
            InputTable = replaceSpacesWithUnderscores(InputTable);
            
            if VMagnet_Layers==1
                % Absolute  (상수 값)
                obj.MagnetThickness_Array = [InputTable.L1_Magnet_Thickness];
                % obj.BridgeThickness_Array = [tbl.L1_Bridge_Thickness];
                obj.PoleVAngle_Array = [InputTable.L1_Pole_V_Angle];
                % obj.VShapeMagnetPost_Array = [tbl.L1_Magnet_Post];
                obj.MagnetSeparation_Array = [InputTable.L1_Magnet_Separation];
                % obj.VShapeMagnetSegments_Array = [tbl.L1_Magnet_Segments];

                % Ratio (Interior V(Web) BPMRotor =11 (비율 값)
                obj.RatioArray_PoleArc = [InputTable.L1_Pole_Arc];
                obj.RatioArray_WebThickness = [InputTable.L1_Web_Thickness];
                obj.RatioArray_VWebBarWidth = [InputTable.L1_Magnet_Bar_Width];
                obj.RatioArray_WebLength = [InputTable.L1_Web_Length];
            elseif VMagnet_Layers==2
                % Absolute  (상수 값)
                obj.MagnetThickness_Array = [InputTable.L1_Magnet_Thickness, InputTable.L2_Magnet_Thickness];
                % obj.BridgeThickness_Array = [tbl.L1_Bridge_Thickness, tbl.L2_Bridge_Thickness];
                obj.PoleVAngle_Array = [InputTable.L1_Pole_V_Angle, InputTable.L2_Pole_V_Angle];
                % obj.VShapeMagnetPost_Array = [tbl.L1_Magnet_Post, tbl.L2_Magnet_Post];
                obj.MagnetSeparation_Array = [InputTable.L1_Magnet_Separation, InputTable.L2_Magnet_Separation];
                % obj.VShapeMagnetSegments_Array = [tbl.L1_Magnet_Segments, tbl.L2_Magnet_Segments];

                % Ratio (Interior V(Web) BPMRotor =11 (비율 값)
                obj.RatioArray_PoleArc = [InputTable.L1_Pole_Arc, InputTable.L2_Pole_Arc];
                obj.RatioArray_WebThickness = [InputTable.L1_Web_Thickness, InputTable.L2_Web_Thickness];
                obj.RatioArray_VWebBarWidth = [InputTable.L1_Magnet_Bar_Width, InputTable.L2_Magnet_Bar_Width];
                obj.RatioArray_WebLength = [InputTable.L1_Web_Length, InputTable.L2_Web_Length];
            end
        end
    end
end
