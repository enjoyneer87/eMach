function isSimiliar=difftol(a,b,tolerance)
    if nargin<3
    tolerance=1e-5
    end
    isSimiliar=abs(a-b)<tolerance;

end