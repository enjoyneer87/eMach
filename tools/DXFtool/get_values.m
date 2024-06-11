function values = get_values(code_no,eCodes,eValues)
% get values for current entity during reading of file
    
    values = eValues(eCodes==code_no);
    
end
