function RegionDataTable=getAllGeomSketchDataTable(app,AssembleName)
   %[WIP] sketchAssemble=getGeomSketchAssembleTable(AssembleName,app) 와 중복
    % getGeomSketchAssembleTable>getStatorGeomSketchData>getSkecthDataTableFromCurrentSelection>

  %% Assembly의 Item 목록 가져오기 Struct 2 Table 

    % AssemObjStruct=getStatorGeomSketchData(app,AssembleName);
    refObjTable             =getGeomSketchAssembleTable(AssembleName,app);

   % AssemObjStruct              =getSkecthDataTableFromCurrentSelection(app);
    % refObjTable                 =struct2table(AssemObjStruct);

    %% Line & Arc & RegionItem & Vertex
    % AssemLineTable    =getLineTable(refObjTable);
    % AssemArcTable     =getArcTable(refObjTable);
    % AssemRegionTable  =getRegionItemTable(refObjTable);
    
    AssemLineDataTable             =getArcDataTable(refObjTable,app)                        ;
    AssemArcDataTable              =getLineDataTable(refObjTable,app)                       ;
    AssemRegionItemDataTable       =getRegionItemDataTable(refObjTable,AssembleName,app)    ;                    
        
       
    %% StatorSketchRefObjStr is all object of CurrentSelection
    
    

    
    %% getRegionDataArea -> replace function that get all data
    RegionData=getRegionDataArea(StatorSketchRefObjStr,app);



    %%
    % StatorSketchRefObjStr=getStatorGeomSketchData(app);
    % refObjTable=struct2table(StatorSketchRefObjStr);


    %%
    geomApp=app.CreateGeometryEditor(0);
    geomApp.GetDocument().GetAssembly().GetItem(AssembleName).OpenSketch();
    geomDocu=geomApp.GetDocument();
    sel=mkSelectionObj(app,1);
    newStruct=struct();
    %% Selection Object
    sel=geomDocu.GetSelection;
    NumSelections=sel.Count;
    % NumSelections=length(StatorSketchRefObjStr);
    % NumSelections=length(sel);

    %% getDataFromSketchRefObj
    for SelIndex=1:NumSelections
    sel.Clear;
    % Area 
    sel.AddReferenceObject(StatorSketchRefObjStr(SelIndex).ReferenceObj);
    geomDocuVolManager=geomDocu.GetVolumeCalculationManager();
    newStruct(SelIndex).Area=geomDocuVolManager.CalculateArea;
    % getLineData

    % getArcData


    end

 
    %%
    ItemDataTable=struct2table(RegionData);
    RegionDataTable=[refObjTable ItemDataTable];


end