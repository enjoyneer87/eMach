function CurItem=convertRefObj2Item(refObj,app)
    sel=mkSelectionObj(app);
    sel.AddReferenceObject(refObj);  % Selection Object
    CurItem=sel.Item(0)                                      ;  % get sketchArc
end