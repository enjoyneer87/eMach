function settingTable=defMCADDXFExportSettingVariable()
        DXFView_Export                          =   0; 
        STL_FormatOptions                       =   0; 
        DXFOption_WireInsulation                =   1; 
        GeometryExportFormat                    =   0; 
        DXFOption_Conductors                    =   1; 
        DXFOption_SlotLiner                     =   1; 
        DXFComponent_Housing                    =   0; 
        DXFComponent_Stator                     =   1; 
        DXFOption_ClosedMagnetGap               =   1;         
        DXFOption_ClosedSlotOpening             =   1;         
        DXFOption_SeparateCoils                 =   1;         
        DXFOption_SegmentOutlines               =   1;         
        DXFOption_CoilDivider                   =   1; 
        DXFOption_SlotDucts                     =   1; 
        DXFWindingOption_SlotTeeth              =   1; 
        DXFComponent_Rotor                      =   1; 
    data = {
        'DXFView_Export'                        ,   DXFView_Export             
        'STL_FormatOptions'                     ,   STL_FormatOptions          
        'DXFOption_WireInsulation'              ,   DXFOption_WireInsulation   
        'GeometryExportFormat'                  ,   GeometryExportFormat       
        'DXFOption_Conductors'                  ,   DXFOption_Conductors       
        'DXFOption_SlotLiner'                   ,   DXFOption_SlotLiner       
        'DXFComponent_Housing'                  ,   DXFComponent_Housing       
        'DXFComponent_Stator'                   ,   DXFComponent_Stator        
        'DXFOption_ClosedMagnetGap'             ,   DXFOption_ClosedMagnetGap       
        'DXFOption_ClosedSlotOpening'           ,   DXFOption_ClosedSlotOpening     
        'DXFOption_SeparateCoils'               ,   DXFOption_SeparateCoils         
        'DXFOption_SegmentOutlines'             ,   DXFOption_SegmentOutlines       
        'DXFOption_CoilDivider'                 ,   DXFOption_CoilDivider     
        'DXFOption_SlotDucts'                   ,   DXFOption_SlotDucts       
        'DXFWindingOption_SlotTeeth'            ,   DXFWindingOption_SlotTeeth
        'DXFComponent_Rotor'                    ,   DXFComponent_Rotor        

    };
        settingTable = cell2table(data, 'VariableNames', {'AutomationName', 'CurrentValue'});

end