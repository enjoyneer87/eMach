function checkType=checkfindType(findType)
        if isstring(findType)||ischar(findType)
            checkType=contains(findType,'exact','IgnoreCase',true);
        elseif isnumeric(findType)
            checkType=findType;
        elseif islogical(findType)
            checkType=findType;
        else
            checkType=0;
        end
end