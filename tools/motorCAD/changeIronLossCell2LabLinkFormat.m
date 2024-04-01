function modifiedStrings = changeIronLossCell2LabLinkFormat(inputStrings)
    modifiedStrings = inputStrings;

    for i = 1:numel(inputStrings)
        str = inputStrings{i};

        % Find 'Hysteresis Iron Loss' and 'Stator Back Iron' and add parentheses
        startIndex = strfind(str, 'Iron Loss');
        % 'Iron Loss'와 'Hysteresis' 또는 'Eddy' 사이의 문자열 찾기
        hysteresisIndex = strfind(str, 'Hysteresis');
        eddyIndex = strfind(str, 'Eddy');
        
        if ~isempty(startIndex) && (~isempty(hysteresisIndex) || ~isempty(eddyIndex))
            if ~isempty(hysteresisIndex) && startIndex(end) < hysteresisIndex(1)
                foundString = str(startIndex(end)+10:hysteresisIndex(1)-2);
                type='Hysteresis';
            elseif ~isempty(eddyIndex) && startIndex(end) < eddyIndex(1)
                foundString = str(startIndex(end)+10:eddyIndex(1)-2);
                type='Eddy';
            else
                foundString = '';
            end
            
            if ~isempty(foundString)
                foundString = ['(',foundString,')'];
                fprintf('찾은 문자열: %s\n', foundString);
                newStr = [type,' Iron Loss ',foundString];
            else
                fprintf('일치하는 문자열을 찾지 못했습니다.\n');
                newStr = [type,' Iron Loss'];
            end
        else
            fprintf('일치하는 문자열을 찾지 못했습니다.\n');
        end
        modifiedStrings{i}=newStr;
    end

end
