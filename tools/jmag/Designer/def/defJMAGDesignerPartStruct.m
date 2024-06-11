function PartStruct=defJMAGDesignerPartStruct()
    partIndex=1;
    
    PartStruct.object                             =[];
    PartStruct(partIndex).partIndex               =[];
    PartStruct(partIndex).Name                    =[];                                                                  
    PartStruct(partIndex).Area                    =[];                                                                  
    PartStruct(partIndex).Edge                    =[];                                                                  
    PartStruct(partIndex).Vertex                  =[];     
    
    PartStruct(partIndex).VertexMaxThetaPos        =[];
    PartStruct(partIndex).VertexMinThetaPos        =[];
    PartStruct(partIndex).VertexMaxRPos            =[];
    PartStruct(partIndex).VertexMinRPos            =[];
    
    % PartStruct(partIndex).CentroidPosition.Obj    =[];                                                                  
    % PartStruct(partIndex).CentroidPosition.X      =[];                                                                  
    % PartStruct(partIndex).CentroidPosition.Y      =[];                                                                  
    % PartStruct(partIndex).CentroidPosition.Z      =[];                                                                  
    % PartStruct(partIndex).CentroidPosition.T      =[];                         
    % PartStruct(partIndex).CentroidPosition.R      =[];                         
    % PartStruct(partIndex).CentroidPosition.T      =[];  
    
    PartStruct(partIndex).CentroidX                 =[];
    PartStruct(partIndex).CentroidY                 =[];
    PartStruct(partIndex).CentroidZ                 =[];
    PartStruct(partIndex).CentroidR                 =[];
    PartStruct(partIndex).CentroidTheta             =[];    
    
    
    % PartStruct(partIndex).CentroidPosition.     =[];                                                                  
    PartStruct(partIndex).FaceColor               =[];                                                                  


end