function SplaidRefObject=devConvertMCADSatuMap2DataDqMap(SatuMap_SplaidRef)
    % object make
    HDEVdata=DataDqMap(6);

    %% MCAD Saturation Map Mat 2 eMach Class DataDqMap
    HDEVdata.current_dq_map.id=SatuMap_SplaidRef.MatData.Id_Peak(:,1)';
    HDEVdata.current_dq_map.iq=SatuMap_SplaidRef.MatData.Iq_Peak(1,:)';
    HDEVdata.flux_linkage_map.in_d=SatuMap_SplaidRef.MatData.Flux_Linkage_D' ;
    HDEVdata.flux_linkage_map.in_q=SatuMap_SplaidRef.MatData.Flux_Linkage_Q' ;
    HDEVdata.file_name=SatuMap_SplaidRef.fileName;
    SplaidRefObject=HDEVdata;
end