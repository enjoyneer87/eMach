function settingTable=defMCADDXFExportSettingVariable(Part,isConductor)
if nargin<2
    isConductor=1;
end

if isConductor==1
            DXFOption_Conductors                    =   1; 
elseif isConductor==0
            DXFOption_Conductors                    =   0; 
end
    if contains(Part,'Stator','IgnoreCase',true)
            DXFComponent_Stator                     =   1;
            DXFComponent_Rotor                      =   0; 
            DXFView_Export                          =   3; 
            DXFOption_WireInsulation                =   0; 
            DXFOption_SlotLiner                     =   0; 
            DXFOption_ClosedSlotOpening             =   1;         
            DXFOption_SeparateCoils                 =   0;         
            DXFOption_CoilDivider                   =   0; 
            DXFWindingOption_SlotTeeth              =   1; 
            DXFOption_SlotDucts                     =   0; 
    
            
    elseif  contains(Part,'Rotor','IgnoreCase',true)
            DXFComponent_Stator                     =   0;
            DXFComponent_Rotor                      =   1; 
            DXFView_Export                          =   4; 
            DXFOption_WireInsulation                =   0; 
            DXFOption_SlotLiner                     =   0; 
            DXFOption_ClosedSlotOpening             =   1;         
            DXFOption_SeparateCoils                 =   0;         
            DXFOption_CoilDivider                   =   0; 
            DXFWindingOption_SlotTeeth              =   1; 
            DXFOption_SlotDucts                     =   0; 
    
    end
            STL_FormatOptions                       =   0; 
            GeometryExportFormat                    =   0; 
            DXFComponent_Housing                    =   0;  
            DXFOption_ClosedMagnetGap               =   1;         
            DXFOption_SegmentOutlines               =   1;         
            DXFFileName                             =  '';
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
            'DXFFileName'                           ,   DXFFileName
        };
            settingTable = cell2table(data, 'VariableNames', {'AutomationName', 'CurrentValue'});

end