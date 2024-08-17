function NewG = dispDepSpecificNode(NodeName)
%
%  
% <DESCRIPTION>
% Extract SpecificNode dependency From dependency graph By dhkim.
% NodeName='acceleration_sim'
foldername = pwd;

G = load([strrep(foldername, filesep, '/') '/.dependency/dependency.mat'], 'G');
G = G.G;
% load('Z:\01_Codes_Projects\VehicleSystem\git_AuVECoDE\01_MAIN_functions\.dependency\dependency.mat')
WholeNodes = splitvars(G.Edges, 'EndNodes');
%% output
% InFunctionNode : 이 함수에서 호출하는 함수 Functions which are called in this Node Function
% OutFunctionNode: 이 함수를 호출하는 함수 Functions which call this Node Function

%% 
% idx = find((Nodes.EndNodes_2==172));
% coupledNode=Nodes.EndNodes_1(idx)
% MainFunctionNode=G.Nodes.Short_Name(coupledNode)
% 
% load('Z:\01_Codes_Projects\VehicleSystem\git_AuVECoDE\.dependency\dependency.mat')
% WholeNodes = splitvars(G.Edges, 'EndNodes');

% Mainidx=find(contains(G.Nodes.Row,NodeName));
% if ~(length(Mainidx)==1)
NodeName = replaceUnderscoresWith(NodeName);
Mainidx = find(strcmp(G.Nodes.Short_Name, NodeName));
% end
% G.Nodes.Short_Name(Mainidx);

% OutFunctionNode: Functions which call this Node Function
idx = find((WholeNodes.EndNodes_1 == Mainidx));
coupledNode = WholeNodes.EndNodes_2(idx);
OutFunctionNode = G.Nodes.Row(coupledNode);

% InFunctionNode: Functions which are called in this Node Function
idx2 = find((WholeNodes.EndNodes_2 == Mainidx));
coupledNode2 = WholeNodes.EndNodes_1(idx2);
InFunctionNode = G.Nodes.Row(coupledNode2);

% Node 제거 
keepNode = unique([InFunctionNode; OutFunctionNode]);
keepNode =[keepNode; G.Nodes.Row(Mainidx)];
removeNodesIdx = setdiff(G.Nodes.Row, keepNode);



G = load([strrep(foldername, filesep, '/') '/.dependency/dependency.mat'], 'G');
G = G.G;
G.Nodes.Name=G.Nodes.Row

names=G.Nodes.Row(removeNodesIdx)
G = rmnode(G, names);

% 
% % 행을 제외한 인덱스 찾기
% keepEdgesIdx = union(idx, idx2);
% removeEdgesIdx = setdiff(1:height(G.Edges), keepEdgesIdx);
% G= rmedge(G,,removeEdgesIdx)
% G.Edges(removeEdgesIdx, :) = [];


% % Removing the rows corresponding to InFunctionNode and OutFunctionNode from G.Edges
% rowsToRemove = ismember(G.Edges.EndNodes, [coupledNode; coupledNode2], 'rows');
% G.Edges(rowsToRemove, :) = [];
% 
% % Removing the corresponding nodes from G.Nodes
% nodesToRemove = unique([coupledNode; coupledNode2]);
% G.Nodes(nodesToRemove, :) = [];
% 
save([strrep(foldername, filesep, '/') '/.dependency/dependency.mat'], 'G');
NewG=G
end