function RegionTablePerType = detStatorRegionTablePerType(RegionDataTable)


% Name4Object         =   'otherSlotArea';
% TableIndex4RegionTable=table();
otherSlotAreaTable  =   table();
InsulationAreaTable =   table();
CoreAreaTable       =   table();
ConductorTable      =   table();


%%
%% 
    for Index4RegionTable=1:height(RegionDataTable)  
        if strcmp(RegionDataTable.Type{Index4RegionTable},'RegionItem')
            %% StatorCore
            if strcmp(RegionDataTable.Name{Index4RegionTable},'StatorCore')
            CoreAreaTable=[CoreAreaTable;RegionDataTable(Index4RegionTable,:)];
            end
            if contains(RegionDataTable.Name{Index4RegionTable},'Insulation')
            InsulationAreaTable=[InsulationAreaTable;RegionDataTable(Index4RegionTable,:)];
            end
            %% Conductor
            if contains(RegionDataTable.Name{Index4RegionTable},'Conductor','IgnoreCase',true)
            ConductorTable=[ConductorTable;RegionDataTable(Index4RegionTable,:)];
            end
            %% Other
            if ~strcmp(RegionDataTable.Name{Index4RegionTable},'StatorCore')&&~contains(RegionDataTable.Name{Index4RegionTable},'Conductor') ||contains(RegionDataTable.Name{Index4RegionTable},'Housing') 
            % TableIndex4RegionTable = [TableIndex4RegionTable; table(Index4RegionTable) ];    
            otherSlotAreaTable=[otherSlotAreaTable;RegionDataTable(Index4RegionTable,:) ];
           
            end
        end
    end

%%
RegionTablePerType.otherSlotAreaTable       =otherSlotAreaTable       ;         
RegionTablePerType.InsulationAreaTable      =InsulationAreaTable      ;
RegionTablePerType.CoreAreaTable            =CoreAreaTable      ;         
RegionTablePerType.ConductorTable           =ConductorTable           ;
% RegionTablePerType.TableIndex4RegionTable           =TableIndex4RegionTable;
end

