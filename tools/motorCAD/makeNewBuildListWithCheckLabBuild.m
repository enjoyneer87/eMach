function newBuildList=makeNewBuildListWithCheckLabBuild(BuildList)
newBuildList = cell(0, 3); % 빈 newBuildList를 미리 초기화합니다.

for i = 1:length(BuildList)
    checkBuild = strsplit(BuildList{i, 1}, '=');
    if ~isempty(checkBuild{2})
        % checkBuild{2}가 비어 있지 않을 때만 데이터를 추가합니다.
        newBuildList(end + 1, :) = BuildList(i, :);
    end
end

end