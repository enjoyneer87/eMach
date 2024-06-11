function writeDXF(filename, DXFvar)
    entitiesStruct=DXFvar.entities;
    % Open a new file for writing
    fid = fopen(filename, 'w');
    
    % Write the DXF header
    fprintf(fid, '0\nSECTION\n2\nHEADER\n0\nENDSEC\n');
    fprintf(fid, '0\nSECTION\n2\nTABLES\n0\nENDSEC\n');
    fprintf(fid, '0\nSECTION\n2\nBLOCKS\n0\nENDSEC\n');
    fprintf(fid, '0\nSECTION\n2\nENTITIES\n');
    
    % Loop through each entity and write to the DXF file
    for i = 1:length(entitiesStruct)
        entity = entitiesStruct(i);
        
        if ~isempty(entity.line)
            if iscell(entity.layer)
                entity.layer=entity.layer{:};
            end
            fprintf(fid, '0\nLINE\n8\n%s\n', entity.layer);
            fprintf(fid, '10\n%f\n20\n%f\n30\n0.0\n', entity.line(1), entity.line(2));
            fprintf(fid, '11\n%f\n21\n%f\n31\n0.0\n', entity.line(3), entity.line(4));
        end
        
        if ~isempty(entity.arc)
            fprintf(fid, '0\nARC\n8\n%s\n', entity.layer);
            fprintf(fid, '10\n%f\n20\n%f\n30\n0.0\n', entity.arc(1), entity.arc(2));
            fprintf(fid, '40\n%f\n', entity.arc(3));
            fprintf(fid, '50\n%f\n', entity.arc(4));
            fprintf(fid, '51\n%f\n', entity.arc(5));
        end
    end
    
    % Write the DXF footer
    fprintf(fid, '0\nENDSEC\n0\nEOF\n');
    
    % Close the file
    fclose(fid);
end
