function MotFilePath=mkMotFilePathFromMotFileListTable(motMatFileListTable,FileIndex)
MotFilePath = strcat(motMatFileListTable.ParentPath{FileIndex},motMatFileListTable.FileDir{FileIndex},'\',motMatFileListTable.FileName{FileIndex});

end