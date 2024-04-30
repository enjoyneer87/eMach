function value=getValuesMotDatainCellFormat(celldata)
    a=extractAfter(celldata,'=');
    value=str2double(a);
end