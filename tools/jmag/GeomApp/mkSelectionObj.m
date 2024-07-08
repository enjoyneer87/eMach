function sel=mkSelectionObj(geomApp,~)

    %    Type of geometry to be selected
    % NOFILTER = 0 : Do not use filter (selects everything in the position) *Default
    % VERTEX = 1 : Point
    % EDGE = 2 : Edge, Reference line
    % FACE = 4 : Face
    % LUMP = 8 : Part
    % REGION_VERTEX = 16 : Region vertex
    % REGION_EDGE = 32 : Region edge
    % REGION = 64 : Region
    % PLANE = 128 : Reference Plane
    % POINT = 256 : Reference point

    %% Need to OpenSketch before excute This Function
    % geomApp=app.CreateGeometryEditor(0);
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
     geomApp=geomApp.CreateGeometryEditor(0);
    end
    
    %%
    % geomApp.visible
    geomDocu=geomApp.GetDocument();
    sel=geomDocu.GetSelection;
    % sel.Add
    % 
    if nargin<2
        geomApp.Hide;
        sel.Clear;
    else
        geomView=geomApp.View();
        % geomView.SetSelectionFilter(int32(3+4+8))
        xstart=0;
        ystart=0;
        zstart=0;
        xMax=4*10e6;
        yMax=4*10e6;
        zMax=4*10e6;
        % geomView.SelectByCircleWorldPos(xstart, ystart,zstart, xMax, yMax, zMax, 0);

    %% [WIP]

    % geomView.SelectAtCircleDlg()
    boolvis_item=true;
    is_height=true;
    filter=int32(0);
    center_x              =  0;
    center_y              =  0    ;
    center_z              =  0    ;
    center_axis_x         =  0        ;
    center_axis_y         =  0        ;
    center_axis_z         =  0        ;
    x_axis_x              =  0    ;
    x_axis_y              =  0    ;
    x_axis_z              =  0    ;
    outerRadius           =  10e6    ;
    innerRadius           =  0    ;
    startAngle            =  0    ;
    top                   =0  ;
    bottom                =0      ;
    EndAngle              =  360   ;
    geomView.SelectAtCircleDlg(center_x, center_y,center_z,center_axis_x,center_axis_y,center_axis_z,x_axis_x,x_axis_y,x_axis_z,outerRadius,innerRadius,startAngle,EndAngle,is_height,top,bottom,boolvis_item,filter)
    
    %%
    sel=geomDocu.GetSelection;
    end

    %%

    % geomApp.GetDocument().GetAssembly().GetItem().OpenSketch();
    % geomView.SetSelectionFilter('Region')
end