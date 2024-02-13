function AssemRegionTable=getRegionItemDataTable(refObjTable,AssembleName,geomApp)
%% Init
%% check App or Geometry Editor
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
        geomApp=geomApp.CreateGeometryEditor(0);
        % geomApp.Show
    end


geomApp.Hide;
geomApp.GetDocument().GetAssembly().GetItem(AssembleName).OpenSketch();
geomDocu=geomApp.GetDocument();

%%  Get RegionItemTable
AssemRegionTable  =getRegionItemTable(refObjTable);

% sel=geomDocu.GetSelection;
% % NumSelections=sel.Count;
NumSelections=height(AssemRegionTable);
%% 면적 구하기 For 문 
    for SelIndex=1:NumSelections
%% Selection Object
        % mk current Selection
        % CurItem=convertRefObj2Item(AssemRegionTable.ReferenceObj(SelIndex),geomApp);     
        %% 면적 구하기 
                
        % if CurItem.IsValid
        if strcmp(AssemRegionTable.Type(SelIndex),'RegionItem') 
           geomDocu=geomApp.GetDocument;
           sel=geomDocu.GetSelection  ;           
           sel.AddReferenceObject(AssemRegionTable.ReferenceObj(SelIndex));                           % Selection Object    
           geomDocuVolManager             =geomDocu.GetVolumeCalculationManager();
           AssemRegionTable.Area(SelIndex)=geomDocuVolManager.CalculateArea;        
        else
            AssemRegionTable.Area(SelIndex)=0;
        end
        % else
        % RegionArray(SelIndex,1)=refObjTable(SelIndex).Area;
        % AssemRegionTable.Area(SelIndex)=0.0001;
        % end
        sel.Clear;
    end
% sel.Clear
geomApp.Show

end
