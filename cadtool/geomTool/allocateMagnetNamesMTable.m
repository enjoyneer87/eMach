function regionTable = allocateMagnetNamesMTable(regionTable)
    %% temp
    % regionTable=RotorAssemRegionTable;
    %%
    % Define a tolerance for grouping distances into layers  
    tolerance = 0.001;

    % Find the regions that correspond to magnets
    MagnetRegionIndexs = getMagnetRegion(regionTable);

    % Get unique distances (radii) from the center to determine layers
    MagnetDistancePerLayer = uniquetol(regionTable.distanceRFromCenter(MagnetRegionIndexs), tolerance);

    % Create an array for the magnet layers
    MagnetLayers = 1:length(MagnetDistancePerLayer);

    % Initialize the Name column in regionTable if it does not exist
    if ~ismember('Name', regionTable.Properties.VariableNames)
        regionTable.Name = strings(height(regionTable), 1);
    end

    % Allocate magnet names per layer number
    for i = 1:length(MagnetLayers)
        % Find the indices of the regions in the current layer
        layerIndices = MagnetRegionIndexs(ismembertol(regionTable.distanceRFromCenter(MagnetRegionIndexs), MagnetDistancePerLayer(i), tolerance));

        % Assign the magnet name to these regions
        magnetName = ['Magnet', num2str(MagnetLayers(i))];
        for magnetIndex=1:length(layerIndices)
        regionTable.Name{layerIndices(magnetIndex)}= magnetName;
        end
    end
end