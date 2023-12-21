function sketchs=ImportDXF2Geom(dxfList2Import,app)
    % app.LaunchGeometryEditor();
    geomApp = app.CreateGeometryEditor(0);
    geomApp.Show;
    geomDocu=geomApp.GetDocument();
    geomAssem=geomDocu.GetAssembly();

    %%
    sketchs=struct();% struct 4 geomApp object
    


 %    if length(dxfList2Import)>1
 %    ItemList={"Stator","Rotor"};
 % %%
 %    % Define Sketch Names
 % 
 %    sketchs(1).sketchName=ItemList{1};
 %    sketchs(2).sketchName=ItemList{2};
 %    else
 %    sketchs(1).sketchName='Stator';
 %    end

 %% 
  if length(dxfList2Import)==2
 
      % 현재 geomAssem의  item 갯수 확인
      % merge하고 이름동시에 


   
    % i가 유효 해당 dxf이어야됨

    %% Stator
    geomApp.Merge(dxfList2Import(1).dxfPath);

    NumItems=geomAssem.NumItems;
    for i=1:NumItems    

        if i==1
        sketchs(i).object          = geomAssem.GetItem('2DSketch');
        IsValid=sketchs(i).object.IsValid;
        else
        sketchs(i).object          = geomAssem.GetItem(['2DSketch.',num2str(i)]);
        IsValid=sketchs(i).object.IsValid;
        end

        if IsValid==1
        sketchs(i).object.SetProperty("Name", dxfList2Import(1).sketchName)
        end
    end

    %% Rotor
    geomApp.Merge(dxfList2Import(2).dxfPath);

    NumItems=geomAssem.NumItems;
    for i=1:NumItems    

        if i==1
        sketchs(i).object          = geomAssem.GetItem('2DSketch');
        IsValid=sketchs(i).object.IsValid;
        else
        sketchs(i).object          = geomAssem.GetItem(['2DSketch.',num2str(i)]);
        IsValid=sketchs(i).object.IsValid;
        end

        if IsValid==1
        sketchs(i).object.SetProperty("Name", dxfList2Import(2).sketchName)
        end
    end


end