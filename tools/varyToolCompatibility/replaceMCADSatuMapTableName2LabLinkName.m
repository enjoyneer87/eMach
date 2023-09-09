function satuaMapTable=replaceMCADSatuMapTableName2LabLinkName(satuaMapTable)
        oldVarNames = satuaMapTable.Properties.VariableNames;
        newVarNames = strrep(oldVarNames, "Stator Current Line Peak", 'Is');
        newVarNames = strrep(newVarNames, "Phase Advance", 'Current Angle');
        satuaMapTable.Properties.VariableNames=newVarNames;
    % % 'Is'
    % % 'Current Angle',
    % 'Flux Linkage D',
    % 'Flux Linkage Q',
    % 'Magnet Loss',
    % 'Banding Loss',
    % 'Sleeve Loss',
    % 'AC Copper Loss (C1)',
    % 'AC Copper Loss (C2)'
    % 'Stator Current Phase Peak',
    % 'Phase Advance',
end

