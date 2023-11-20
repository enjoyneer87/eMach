function sketchs=ImportDXF2Geom(dxfList2Import,app)
    app.LaunchGeometryEditor();
    geomApp = app.CreateGeometryEditor(1);
    geomApp.Show;
    geomDocu=geomApp.GetDocument();
    geomAssem=geomDocu.GetAssembly();

    sketchs=struct();
    ItemList={"Stator","Rotor"};

 %%
    % Define Sketch Names
    sketchs(1).sketchName=ItemList{1};
    sketchs(2).sketchName=ItemList{2};

    for i=1:length(dxfList2Import)  
        geomApp.Merge(dxfList2Import(i).dxfPath);
        if i==1
        sketchs(i).object          = geomAssem.GetItem('2DSketch');
        else
        sketchs(i).object          = geomAssem.GetItem(['2DSketch.',num2str(i)]);
        end
        sketchs(i).object.SetProperty("Name", sketchs(i).sketchName)
    end
end