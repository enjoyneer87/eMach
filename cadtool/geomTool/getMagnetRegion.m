function MagnetRegionIndexs=getMagnetRegion(regionTable)

MagnetRegionIndexs = findRegionsWithNoOuterArcs(regionTable);
if isempty(MagnetRegionIndexs)
MagnetRegionIndexs = findRegionsWith2LinePairN2ArcPair(regionTable);
fprintf('Regions where Magnet is: %s\n', num2str(MagnetRegionIndexs'));
end

end