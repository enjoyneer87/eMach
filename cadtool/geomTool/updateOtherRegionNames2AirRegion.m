function regionTable = updateOtherRegionNames2AirRegion(regionTable)
    % List of names that should not be changed
    namesToKeep = {'shaft', 'Rotorcore', 'Magnet','Sleeve'};
    
    % Iterate over each row in regionTable
    for i = 1:height(regionTable)
        name = regionTable.Name{i};
        if ~contains(name, namesToKeep,"IgnoreCase",true)
            regionTable.Name{i} = 'airRegion';
        end
    end
end