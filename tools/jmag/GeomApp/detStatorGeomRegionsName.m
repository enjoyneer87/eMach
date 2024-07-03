function RegionListExcept2Delete=detStatorGeomRegionsName(RegionTablePerType,Name2Change)
             %% StatorCore
            if strcmp(Name2Change,'StatorCore')
                  RegionListExcept2Delete    = RegionTablePerType.CoreAreaTable.Name;
            %% Conductor
            elseif contains(Name2Change,'Conductor')
                RegionListExcept2Delete    = RegionTablePerType.ConductorTable.Name;
            %% Other
            elseif contains(Name2Change,'Insulation')
                RegionListExcept2Delete    = RegionTablePerType.InsulationAreaTable.Name;
            elseif contains(Name2Change,'Housing')
                RegionListExcept2Delete    = RegionTablePerType.HousingTable.Name;
            elseif contains(Name2Change,'otherSlotArea')
                RegionListExcept2Delete    = RegionTablePerType.otherSlotAreaTable.Name;
            end        
end