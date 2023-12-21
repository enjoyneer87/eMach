function CurItem=convertRefObj2Item(refObj,app)
    % RefObj2 Selection Item
    % mkSelectionObj Need to OpenSketch before excute 
    sel=mkSelectionObj(app);
    sel.AddReferenceObject(refObj);                           % Selection Object
    
    CurItem=sel.Item(0)                                      ; % get sketch Item
end