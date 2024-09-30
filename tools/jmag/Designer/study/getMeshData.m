function [ElementID, NodeID,NodeTable, delaunyObj]=getMeshData(app,PartIndex)
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
% sel=JView.GetCurrentSelection;
NumElements=sel.NumElements;

for ElementIndex=1:NumElements
    ElementID(ElementIndex,1)=sel.ElementID(int32(ElementIndex)-1);
end

studyObj=app.GetCurrentStudy;


%% Node ID
JView.SelectElementVertex
sel=getViewCurrentSelection(JView);
NumNodes=sel.NumNodes();
NodeID=zeros(NumNodes,1);
for NodeIndex=1:NumNodes
    NodeID(NodeIndex,1)=sel.NodeID(NodeIndex-1);
end

%% Node Coord
[nodeCoords, DT]=getNodePos(NodeID,studyObj);
% nodeCoords=getNodePos(NodeID,studyObj);
% %% [TB] ElementEdge
% JView.SelectElementEdge
% sel=getViewCurrentSelection(JView);    

%% Element CenterPosition
% IC = incenter(DT);
NodeTable.nodeCoords=nodeCoords;
NodeTable.NodeID    =NodeID    ;
delaunyObj=DT;
end