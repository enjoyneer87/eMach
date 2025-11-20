
function [IdqList] = getQuarterCirclePoints()
    r = 1;  % normalize radius
    IdqList = [ 0,     0;     % origin
               -1,     0;     % -d
                0,     1;     % +q
         -sqrt(2)/2, sqrt(2)/2 ]; % center of arc
end
