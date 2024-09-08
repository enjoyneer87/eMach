function selJMagDesignerObj(app,PartIdList)
    Model=app.GetCurrentModel;
    app.View.ShowMesh();
    sel=Model.CreateSelection();
    if nargin>1
        for PartIndex=1:length(PartIdList)
        sel.SelectPart(PartIdList(PartIndex))
        end
    else
        app.View.ShowAllAirRegions();
        PartStruct     =getJMAGDesignerPartStruct(app);
        PartStruct     =getEdgeVertexIdwithXYZCheck(PartStruct,app);   
        i_Stator_OD=2*max([PartStruct.VertexMaxRPos]);  
        SOD_air = i_Stator_OD/2+0.5;    %[mm]
        SOD_air_cartesian = SOD_air * 0.001; 
        pos_air_xaxis_cart= [SOD_air,0,0]  ;
        SWP_type=3;  % 0x01:Shift    % 0x02:Control   % 0x03:Shift&Control             
        app.View().SelectWorldPos(pos_air_xaxis_cart(1),pos_air_xaxis_cart(2),pos_air_xaxis_cart(3),SWP_type);
    end


end