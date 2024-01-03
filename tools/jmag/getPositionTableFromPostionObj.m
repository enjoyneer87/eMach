function vertexTable=getPositionTableFromPostionObj(PositionObj)
    vertexTable=table();
    vertexTable.Itemobj  =PositionObj                     ;
    % PositionObj=StatorGeomArcTable.StartVertexTableItemobj(1)
    vertexTable.Name     ={PositionObj.GetName}             ;
    vertexTable.Type     ={PositionObj.GetScriptTypeName}   ;
    
    xyzPosition=getPositionStructFromPostionObj(PositionObj);
    [theta,r]=cart2pol(xyzPosition.x,xyzPosition.y);
    totalPosition=xyzPosition;
    totalPosition.r=r;
    totalPosition.theta=rad2deg(theta);
    % xyzPositionTable=struct2table(xyzPosition);
    totalPositionTable=struct2table(totalPosition);
    % vertexTable=[vertexTable xyzPositionTable];
    vertexTable=[vertexTable totalPositionTable];

end