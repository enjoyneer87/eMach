function MCADStruct=defMcadTableStruct()
    ActiveXStr=loadMCadActiveXParameter();
    MCADStruct=ActiveXStr.ActiveXParametersStruct;
end