function displayStructFields(structure, prefix)
    fields = fieldnames(structure);
    for i = 1:length(fields)
        currentField = fields{i};
        if isstruct(structure.(currentField))
            fprintf('%s%s:\n', prefix, currentField);
            displayStructFields(structure.(currentField), [prefix '  ']);
        else
            fprintf('%s%s\n', prefix, currentField);
        end
    end
end