function RegionListExcept2Delete=detRotorGeomRegionsName(RegionTablePerType,Name2Change)
             %% StatorCore
            if strcmp(Name2Change,'RotorCore')
                  RegionListExcept2Delete    = RegionTablePerType.CoreAreaTable.Name;
            %% Conductor
            elseif contains(Name2Change,'Magnet')
                RegionListExcept2Delete    = RegionTablePerType.MagnetTable.Name;
            %% Other
            elseif contains(Name2Change,'Air')
                RegionListExcept2Delete    = RegionTablePerType.AirAreaTable.Name;
            elseif contains(Name2Change,'Band')
                RegionListExcept2Delete    = RegionTablePerType.BandAreaTable.Name;
            elseif contains(Name2Change,'Shaft')
                RegionListExcept2Delete    = RegionTablePerType.ShaftTable.Name;
            end        
end