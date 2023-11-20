function Position=getPositionStructFromPostionObj(PositionObj)
Position.x=PositionObj.GetX;
Position.y=PositionObj.GetY;

if ~strcmp(PositionObj.GetScriptTypeName,'SketchVertex')
Position.z=PositionObj.GetZ;
end

end