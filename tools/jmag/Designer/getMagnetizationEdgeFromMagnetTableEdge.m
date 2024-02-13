function MagnetizationEdgeIndex=getMagnetizationEdgeFromMagnetTableEdge(MagnetTable)

EdgeTableofMagnet=MagnetTable.Edge{:};
tolerance=1e-5;

for EdgeIndex=1:height(EdgeTableofMagnet)

    if EdgeTableofMagnet.midPosition(EdgeIndex,4)-EdgeTableofMagnet.startPosition(EdgeIndex,4)<tolerance
    MagnetizationEdgeIndex=EdgeIndex;
    end
end

end