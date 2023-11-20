function vertexTable=getPositionTableFromPostionObj(PositionObj)
    vertexTable=table();
    vertexTable.Itemobj  =PositionObj                     ;
    vertexTable.Name     ={PositionObj.GetName}             ;
    vertexTable.Type     ={PositionObj.GetScriptTypeName}   ;
    
    xyPosition=getPositionStructFromPostionObj(PositionObj);
    xyPositionTable=struct2table(xyPosition);

    vertexTable=[vertexTable xyPositionTable];
end