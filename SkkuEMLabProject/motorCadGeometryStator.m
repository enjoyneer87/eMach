classdef motorCadGeometryStator
    properties
        slotNumber
        housingDia
        statorLamDia
        slotCornerRadius
        toothTipDepth
        toothTipAngle
        activeVolume
        ratioBore
        ratioSlotDepthParallelTooth
        minBackIronThickness
        ratioToothWidth
        ratioSlotOpeningParallelTooth
        Ratio_Bore                      
        Ratio_SlotWidth
        Ratio_SlotDepth_ParallelSlot
        Ratio_SlotOpening_ParallelSlot

    end
    
    methods
        function obj = motorCadGeometryStator(pStatorSlots, iStatorOD, iSlotCornerRadius, pToothTipDepth, pToothTipAngle, iActiveLength, iSplitRatio, iDepthSlotRatio, pMinThicknessBackIron, iYtoT, iSlotOpRatio)
            obj.slotNumber = pStatorSlots;
            obj.housingDia = iStatorOD + 40;
            obj.statorLamDia = iStatorOD;
            obj.slotCornerRadius = iSlotCornerRadius;
            obj.toothTipDepth = pToothTipDepth;
            obj.toothTipAngle = pToothTipAngle;
            
            % Calculate and set the value for activeVolume using the provided function
            obj.activeVolume = calculateActiveVolume(iStatorOD, iActiveLength);
            
            obj.ratioBore = iSplitRatio;
            obj.ratioSlotDepthParallelTooth = iDepthSlotRatio;
            obj.minBackIronThickness = pMinThicknessBackIron;

        end

        function setMotorCadStatorGeometry(obj, pMinThicknessBackIron)
            [~, slotDepthGetVar] = mcApp.GetVariable('Slot_Depth');
            backIronThickness = calculateBackIronThickness(iStatorOD, iSplitRatio, iDepthSlotRatio, pMinThicknessBackIron);
            disp('Ratio_SlotDepth_ParallelTooth Slot Depth/Stator Lam Thickness(Yoke):', iDepthSlotRatio);
            disp('Contraints Min BackIron(Yoke):', pMinThicknessBackIron, ', Dimension: SlotDepth', slotDepthGetVar);
            
            % Calculate and set the value for ratioToothWidth using the provided function
            [Rint, slotPitch, toothWidth, angleRadianToothWidth, impToothWidthRatio] = calculateImplicitToothWidthRatio(backIronThickness, iYtoT, pToothTipDepth, iStatorOD, iSplitRatio, pStatorSlots);
            obj.ratioToothWidth = impToothWidthRatio;
            disp('### Define Tooth Width ');
            disp('i_YtoT:', iYtoT);
            disp('implicit Tooth_Width_Ratio=', impToothWidthRatio);
            disp('Stator Bore As Contraints=', 2 * Rint, ', Dimension=', toothWidth);
            
            % Calculate and set the value for ratioSlotOpeningParallelTooth using the provided function
            obj.ratioSlotOpeningParallelTooth = iSlotOpRatio;
            maxSlotOpen = calculateSlotOpening(Rint, pToothTipDepth, slotPitch, angleRadianToothWidth);
            slotOpen = maxSlotOpen * iSlotOpRatio;
            disp('### Define Slot Opening');
            disp('Slot Opening/Max Slot Opening', iSlotOpRatio);
            disp('Contraints:', toothWidth, ', Dimension:Slot Opening', slotOpen);
        end
    end

end




