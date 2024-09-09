function Distance=JmagMeasureDistanceFrom(x,y,z,ObjType,Id,StudyObj)

% 
% double Study::MeasureDistanceFrom  ( double  x,  
%   double  y,  
%   double  z,  
%   String &  toType,  
%   Variant &  toID  
%  )  
%  Edge : Edge
% Vertex : Vertex
% Face : Face
% Node : Node
% Element-edge : Element edge
% Element-face : Element face

Distance=StudyObj.MeasureDistanceFrom(x,y,z,ObjType,Id);
% Distance=Model.MeasureDistanceFrom(0,0,0,sel,ObjType)

end
