function plotJMAGMesh(MeshObj)
% MeshObj=TSMesh
    model         =    MeshObj.model         ;
    pdeTriElements=    MeshObj.pdeTriElements;
    pdeNodes      =    MeshObj.pdeNodes      ;


    % tri Mesh plot
    MeshPlot=pdeplot(model.Mesh.Nodes,model.Mesh.Elements);
    MeshPlot.Color=[0.80,0.80,0.80];  % grey
    hold on

    % quad Plot
    if isfield(MeshObj,'pdeQuadElements')
        x = pdeNodes(1,:);
        y = pdeNodes(2,:);
        pdeQuadElements=MeshObj.pdeQuadElements;
        % quadmesh(pdeQuadElements, x, y);
         hh = plotQuadmesh(pdeQuadElements, x, y);
    end

end