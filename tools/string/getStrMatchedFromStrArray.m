function matchedStr=getStrMatchedFromStrArray(StrArray,Str2Search)
    matchedStr = StrArray(contains(StrArray, Str2Search,"IgnoreCase",true));
end

%[appendix]{"version":"1.0"}
%---
