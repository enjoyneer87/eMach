
function deltaFunc = correctionRBF(IdqList, deltaZ)
    Id = IdqList(:,1);
    Iq = IdqList(:,2);
    F = fit([Id, Iq], deltaZ, 'thinplateinterp');
    deltaFunc = @(x,y) F(x,y);
end
