function RotorOnePoleAngle=findRotorOnePoleAngle(Input)

    if istable(Input)
        maxEndVertexTableTheta = -Inf; % Initialize with a very small value
        
        for regionIndex = 1:height(Input)
            SketchList = Input.SketchList{regionIndex};
            RotorGeomArcTable = SketchList{2};
        
            % Update the maximum value if the current one is larger
            if ~isempty(RotorGeomArcTable.EndVertexTabletheta)
                currentMax = max(RotorGeomArcTable.EndVertexTabletheta);
                if currentMax > maxEndVertexTableTheta
                    maxEndVertexTableTheta = currentMax;
                end
            end
        end
    else % PoleNumber
    RotorOnePoleAngle=360/Input;
    end
end