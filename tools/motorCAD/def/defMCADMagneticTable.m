function MCADMagTable=defMCADMagneticTable()
    %% mat파일이 존재해야됨
    ActiveXStr=loadMCadActiveXParameter();
    MCADMagTable=ActiveXStr.ActiveXParametersStruct.Magnetics;
end