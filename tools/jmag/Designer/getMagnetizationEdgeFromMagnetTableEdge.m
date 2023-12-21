function MagnetizationEdgeIndex=getMagnetizationEdgeFromMagnetTableEdge(MagnetTable)

EdgeTableofMagnet=MagnetTable.Edge{:};


for EdgeIndex=1:height(EdgeTableofMagnet)

    if EdgeTableofMagnet.midPosition(EdgeIndex,4) == EdgeTableofMagnet.startPosition(EdgeIndex,4)
    MagnetizationEdgeIndex=EdgeIndex;
    end
end

end