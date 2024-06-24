function [otherDict, otherUnitDict] = convertMCADOtherToStruct(filePath)
    % .mot 파일을 구조체로 변환하고 단위 변환을 위한 구조체 생성
    if ~endsWith(filePath, '.mot')
        error('The file is not a .mot, please select a .mot to convert');
    end
    if ~exist(filePath, 'file')
        error('Error: This file does not exist: %s', filePath);
    end
    
    fid = fopen(filePath, 'rt');
    if fid == -1
        error('File cannot be opened: %s', filePath);
    end
    
    currentSection = '';
    otherDict = struct();
    while ~feof(fid)
        line = strtrim(fgets(fid));
        if isempty(line)
            continue;
        elseif line(1) == '['
            currentSection = line;
            otherDict.(matlab.lang.makeValidName(currentSection)) = struct();
        else
            [key, value] = strtok(line, '=');
            value = strtrim(value(2:end));
            if ~isempty(value)
                numericValue = str2double(value);
                if ~isnan(numericValue)
                    value = numericValue;
                elseif strcmpi(value, 'True')
                    value = true;
                elseif strcmpi(value, 'False')
                    value = false;
                end
                otherDict.(matlab.lang.makeValidName(currentSection)).(matlab.lang.makeValidName(key)) = value;
            end
        end
    end
    fclose(fid);
    
    % 단위 변환을 위한 구조체 생성
    units = otherDict.Units;
    otherUnitDict = struct('m', 1, 'rad', 1, 'deg', pi/180, 'ED', [], 'None', 1, '', 1, '-', 1, '[]', 1);
    if isfield(units, 'Units_Length')
        if strcmp(units.Units_Length, 'mm')
            otherUnitDict.m = 0.001;
        end
    end
    if isfield(otherDict.Dimensions, 'Pole_Number')
        poleNumber = otherDict.Dimensions.Pole_Number;
        otherUnitDict.ED = (2 / poleNumber) * (pi / 180);
    end
end
