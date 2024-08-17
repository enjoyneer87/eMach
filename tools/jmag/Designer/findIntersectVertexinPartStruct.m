function MatchedVertexTable = findIntersectVertexinPartStruct(PartStruct, Name1, Name2)
    if nargin < 2
        Name1 = "StatorCore";
        Name2 = "Insulation";
    end

    isStatorCore = contains({PartStruct.Name}, Name1);
    STCoreIndex = find(isStatorCore);
    isInsulation = contains({PartStruct.Name}, Name2);
    InsulIndex = find(isInsulation);

    % Stator Core와 Insulation에서 공유하는 Vertex 찾기
    if ~isempty(STCoreIndex) && ~isempty(InsulIndex)
        % 두 구조체 배열에서 공유하는 Vertex를 찾아 테이블로 반환

        STCoreVertexIds=PartStruct(STCoreIndex).Vertex.VertexIds;

        [commonVertices, idxStator, idxInsul] = intersect(STCoreVertexIds,...
                                                          PartStruct(InsulIndex(end)).Vertex.VertexIds, 'rows');
        MatchedVertexTable = table(commonVertices, 'VariableNames', {'VertexPosition'});
    elseif ~isempty(STCoreIndex) && isempty(InsulIndex)
        % Stator Core만 존재하는 경우 해당 Vertex를 테이블로 반환
        MatchedVertexTable = struct2table(PartStruct(STCoreIndex).Vertex);
    else
        MatchedVertexTable = table();
    end
end
