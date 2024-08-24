function MeshSizeTable=mkDefaultMeshSizeTable()
    MeshSizeTable=table();
    MeshSizeTable.coreMeshSize     =zeros(0);
    MeshSizeTable.ConductorMeshSize=zeros(0);
    MeshSizeTable.MagnetMeshSize   =zeros(0);
disp('해당 메쉬사이즈는 최소한 입력하세요')
end