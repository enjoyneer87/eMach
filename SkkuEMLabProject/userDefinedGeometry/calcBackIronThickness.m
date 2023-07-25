function statorDepth = calcBackIronThickness(i_Stator_OD, i_Split_Ratio, i_Depth_Slot_Ratio, p_MinThicknessBackIron)
    Rext = i_Stator_OD / 2;
    Rint = (i_Stator_OD * i_Split_Ratio) / 2;
    ThicknessStatorRegion = Rext - Rint;
    BackIronThickness = (1 - i_Depth_Slot_Ratio) * (ThicknessStatorRegion - p_MinThicknessBackIron);
    statorDepth.BackIronThickness=BackIronThickness;
    statorDepth.ThicknessStatorRegion=ThicknessStatorRegion;
    statorDepth.SlotRegionDepth=ThicknessStatorRegion-BackIronThickness-p_MinThicknessBackIron;
end
