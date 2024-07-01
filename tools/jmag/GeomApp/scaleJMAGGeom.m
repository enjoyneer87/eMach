function scaleJMAGGeom(geomApp)
objScale=geomApp.GetDocument().GetAssembly().CreateScale();
objScale.SetProperty("Factor", 2);
objScale.SetProperty("CenterType",int32(2));
geomApp.SaveCurrent();
end