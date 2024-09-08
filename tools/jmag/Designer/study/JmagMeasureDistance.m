function  dist=JmagMeasureDistance(studyObj, fromType, fromID, toType, toID)

    % studyObj: JMAG study 객체
    % fromType: 'Node', 'Edge' 등
    % fromID: 시작점 ID
    % toType: 'Node', 'Edge' 등
    % toID: 끝점 ID

    dist = studyObj.MeasureDistance(fromType, fromID, toType, toID);

end
% double Study::MeasureDistance  ( String &  fromType,  
%   Variant &  fromID,  
%   String &  toType,  
%   Variant &  toID  
%  )   
% 
% 
% Measures the distance between specified entities. 
% Parameters
% fromType 
% Edge : Edge
% Vertex : Vertex
% Face : Face
% Node : Node
% Element-edge : Element edge
% Element-face : Element face
% 
% fromID vertex ID, face ID, edge ID, node ID, element face ID, and element edge ID  
% toType 
% Edge : Edge
% Vertex : Vertex
% Face : Face
% Node : Node
% Element-edge : Element edge
% Element-face : Element face
% 
% toID vertex ID, face ID, edge ID, node ID, element face ID, and element edge ID  
% ReturnsDistance 

    
