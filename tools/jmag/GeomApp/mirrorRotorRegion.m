function mirrorRotorRegion(RotorAssemRegionTable,geomApp)
% Model=app.GetCurrentModel;
% Model.RestoreCadLink()
% geomApp=app.CreateGeometryEditor(0);
AssembleName='Rotor';
geomDocu=geomApp.GetDocument();
geomAssem=geomApp.GetDocument().GetAssembly();
geomView=geomApp.View();
RotorItemObj=geomAssem.GetItem(AssembleName);
RotorItemObj.OpenSketch();

%% PeriodicAngle
% 주기성을 계산합니다.
geomDesignTable=geomDocu.GetDesignTable;
Pole=geomDesignTable.GetEquation('POLES').GetValue;
Slot=geomDesignTable.GetEquation('SLOTS').GetValue;
PeriodicAngle=calcMotorPeriodicity(Pole,Slot);

%% Mirror 
% geomAssem.
categoryStructTable=sortAssemItemTableByType(geomApp,AssembleName);
if isfield(categoryStructTable,'RegionMirrorCopy')
MirrorCopyTable=    categoryStructTable.RegionMirrorCopy;
else 
MirrorCopyTable=[];
end
if isempty(MirrorCopyTable) 
    for RegionIndex=1:height(RotorAssemRegionTable)
        RegionCopyName=[RotorAssemRegionTable.Name{RegionIndex}];
        RotorCopyObj=RotorItemObj.CreateRegionMirrorCopy();
        RotorCopyObj.SetName(RegionCopyName)
        RotorCopyObj.SetProperty("Merge", 1)
        % Select Region
        refRegionIDName     =RotorAssemRegionTable.IdentifierName{RegionIndex};
        RotorCopyObj.SetProperty("Region", refRegionIDName)
        % select Edge
        %% Edge Vector
        vecX=cos(deg2rad(PeriodicAngle/2));
        vecY=sin(deg2rad(PeriodicAngle/2));
        %% Setting
        RotorCopyObj.SetProperty("SymmetryType", int32(1))
        RotorCopyObj.SetProperty("SymmetryVecY", vecY)
        RotorCopyObj.SetProperty("SymmetryVecX", vecX)
        % geomApp.GetDocument().GetAssembly().GetItem("Rotor").CloseSketch()       
    end
end

    geomApp.GetDocument().GetAssembly().GetItem("Rotor").CloseSketch()

end