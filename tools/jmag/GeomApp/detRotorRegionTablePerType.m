function RegionTablePerType = detRotorRegionTablePerType(RegionDataTable)


MagnetTable   =table();
CoreAreaTable =table();
AirAreaTable  =table();
BandAreaTable =table();
ShaftTable   =table(); 


%%
%% 
    for Index4RegionTable=1:height(RegionDataTable)  
        if strcmp(RegionDataTable.Type{Index4RegionTable},'RegionItem')
            %% StatorCore
            if strcmp(RegionDataTable.Name{Index4RegionTable},'RotorCore')
            CoreAreaTable=[CoreAreaTable;RegionDataTable(Index4RegionTable,:)];
            end
            %% Conductor
            if contains(RegionDataTable.Name{Index4RegionTable},'Magnet')
            MagnetTable=[MagnetTable;RegionDataTable(Index4RegionTable,:)];
            end
            if contains(RegionDataTable.Name{Index4RegionTable},'Air')
            AirAreaTable=[AirAreaTable;RegionDataTable(Index4RegionTable,:)];
            end
            if contains(RegionDataTable.Name{Index4RegionTable},'Band')
            BandAreaTable=[BandAreaTable;RegionDataTable(Index4RegionTable,:)];
            end
            if contains(RegionDataTable.Name{Index4RegionTable},'Shaft')
            ShaftTable=[ShaftTable;RegionDataTable(Index4RegionTable,:)];
            end

            %% Other
            % if ~strcmp(RegionDataTable.Name{Index4RegionTable},'StatorCore')&&~contains(RegionDataTable.Name{Index4RegionTable},'Conductor') contains(RegionDataTable.Name{Index4RegionTable},'Housing') 
            % TableIndex4RegionTable = [TableIndex4RegionTable; table(Index4RegionTable) ];    
            % otherSlotAreaTable=[otherSlotAreaTable;RegionDataTable(Index4RegionTable,:) ];
            % 
            % end
        end
    end


%%
RegionTablePerType.MagnetTable        =MagnetTable        ;         
RegionTablePerType.CoreAreaTable      =CoreAreaTable      ;
RegionTablePerType.AirAreaTable       =AirAreaTable ;         
RegionTablePerType.BandAreaTable      =BandAreaTable      ;
RegionTablePerType.ShaftTable         =ShaftTable      ;




end