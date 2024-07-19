function CurItem=convertRefObj2Item(refObj,geomApp)
    % RefObj2 Selection Item
    % mkSelectionObj Need to OpenSketch before excute 
    % sel=mkSelectionObj(app);

%% check App or Geometry Editor
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
    geomApp=geomApp.CreateGeometryEditor(0);
    % geomApp.visible
    end
%%
    geomDocu=geomApp.GetDocument;
    sel=geomDocu.GetSelection  ;
    sel.AddReferenceObject(refObj);                           % Selection Object    -> 동작안되는것도 있는듯
    % if sel.Count~=0
    CurItem=sel.Item(0)                                      ; % get sketch Item
    % elseif sel.Count==0
    % disp('Item이 없습니다')
    % end
    sel.Clear;
end