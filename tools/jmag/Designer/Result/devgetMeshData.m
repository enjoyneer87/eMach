function [ElementID, NodeID]=devgetMeshData(app,PartIndex)
%%dev
% PartIndex=WireIndex
% Select Element
JView=app.View;
JView.HideAll
%% Show Only the Part
Model=app.GetCurrentModel;
Model.SetVisibility(PartIndex,1)
JView.ShowMesh

%% ElementID
JView.SelectElement()
sel=getViewCurrentSelection(JView);
NumElements=sel.NumElements;

for ElementIndex=1:NumElements
ElementID(ElementIndex,1)=sel.ElementID(int32(ElementIndex)-1);
end

%% Node ID
JView.SelectElementVertex
sel=getViewCurrentSelection(JView);
NumNodes=sel.NumNodes();
for NodeIndex=1:NumNodes
NodeID(NodeIndex,1)=sel.NodeID(NodeIndex-1);
end
%% [TB] ElementEdge
JView.SelectElementEdge
sel=getViewCurrentSelection(JView);

end