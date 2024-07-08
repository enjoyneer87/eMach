function RegionListExcept2Delete=detRotorGeomRegionsData(RegionTablePerType,Name2Change)
             %% StatorCore
            if strcmp(Name2Change,'RotorCore')
                  RegionListExcept2Delete.Name    = RegionTablePerType.CoreAreaTable.Name;
                RegionListExcept2Delete.Obj    = RegionTablePerType.CoreAreaTable.ReferenceObj;

            %% Conductor
            elseif contains(Name2Change,'Magnet','IgnoreCase',true)
                RegionListExcept2Delete.Name   = RegionTablePerType.MagnetTable.Name;
                RegionListExcept2Delete.Obj      = RegionTablePerType.MagnetTable.ReferenceObj;

            %% Other
            elseif contains(Name2Change,'Air','IgnoreCase',true)
                RegionListExcept2Delete.Name   = RegionTablePerType.AirAreaTable.Name;
                RegionListExcept2Delete.Obj    = RegionTablePerType.AirAreaTable.ReferenceObj;

            elseif contains(Name2Change,'Band','IgnoreCase',true)
               RegionListExcept2Delete.Name   = RegionTablePerType.BandAreaTable.Name;
               RegionListExcept2Delete.Obj    = RegionTablePerType.RegionListExcept2RefObj.ReferenceObj;

            elseif contains(Name2Change,'Shaft','IgnoreCase',true)
                RegionListExcept2Delete.Name   = RegionTablePerType.ShaftTable.Name;
                RegionListExcept2Delete.Obj    = RegionTablePerType.ShaftTable.ReferenceObj;
            end        
end