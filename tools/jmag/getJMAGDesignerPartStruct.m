function PartStruct=getJMAGDesignerPartStruct(app,NumGroups)
    Model=app.GetCurrentModel();
    if nargin<2
    PartIds=Model.GetPartIDs();
    % elseif        IsGroup==1
    % PartIds=NumGroups;
    end
    PartStruct=defJMAGDesignerPartStruct();
    %% 
    % for partIndex=1:double(PartIds{end})
    for partIndex=1:length(PartIds)    
        PartStruct(partIndex).partIndex                                                          = PartIds{partIndex};
        PartStruct(partIndex).object                                                             = Model.GetPart(PartIds{partIndex});
        if PartStruct(partIndex).object.IsValid
            PartStruct(partIndex).Name                                                               = PartStruct(partIndex).object.GetName     ;
            PartStruct(partIndex).Area                                                               = PartStruct(partIndex).object.Area        ;
            if ~isempty(PartStruct(partIndex).object.GetName)
            PartStruct(partIndex).Edge                                                               = cell2table(PartStruct(partIndex).object.GetEdgeIDs,"VariableNames","EdgeIds")      ;  
            PartStruct(partIndex).Vertex                                                             = cell2table(PartStruct(partIndex).object.GetVertexIDs,'VariableNames',"VertexIds")  ;         
            else
            PartStruct(partIndex).Edge =[];   
            PartStruct(partIndex).Vertex   =[];
            end            
            PartObj                                     =PartStruct(partIndex).object;
            CentroidObj                                 =PartObj.CentroidPosition;
            x                                               =CentroidObj.GetX;                                           
            y                                               =CentroidObj.GetY;                                           
            z                                               =CentroidObj.GetZ;                                           
            PartStruct(partIndex).CentroidX                 =x;
            PartStruct(partIndex).CentroidY                 =y;
            PartStruct(partIndex).CentroidZ                 =z;
            [PartStruct(partIndex).CentroidTheta,PartStruct(partIndex).CentroidR]  =cart2pol(x,y,z);
            PartStruct(partIndex).CentroidTheta                                   =rad2deg(PartStruct(partIndex).CentroidTheta  ) ;                                                  
            % PartStruct(partIndex).CentroidPosition.                        　　　= PartStruct(partIndex).object.CentroidPosition                                             ;                              
            PartStruct(partIndex).FaceColor                                       = PartStruct(partIndex).object.GetColor                                                     ;          
            % PartStruct(partIndex).EdgeMaxRPos   =0;
            % PartStruct(partIndex).EdgeMaxTheaPos=0;
        end
    end
    PartStruct = rmEmptyRowbyField(PartStruct,'Name');
end