function [shapeVars, nonShapeVars] = separateShapeVariables(MCADGEO)
    % Define the criteria for shape variables
    shapeVarCriteria = {'array','thick','front','rear','angle','depth','length', 'width', 'height', 'radius', 'diameter', 'dia', 'area', 'volume', 'ratio'};

    % Get the field names from the MCADGEO structure
    fields = fieldnames(MCADGEO);

    % Convert all field names to lowercase for case-insensitive comparison
    fieldsLower = lower(fields);

    % Create a logical mask where each field matches at least one criterion
    isShape = cellfun(@(f) any(contains(f, shapeVarCriteria)), fieldsLower);

    % Separate based on the mask
    shapeVars = fields(isShape);
    nonShapeVars = fields(~isShape);
end
