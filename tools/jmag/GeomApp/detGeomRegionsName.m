function     RegionListExcept2Delete=detGeomRegionsName(RegionTablePerType,Name2Change)
    if any(contains(fieldnames(RegionTablePerType),'Slot'))
        RegionListExcept2Delete    =detStatorGeomRegionsName(RegionTablePerType,Name2Change);
    else
        RegionListExcept2Delete    =detRotorGeomRegionsName(RegionTablePerType,Name2Change) ;
    end

end