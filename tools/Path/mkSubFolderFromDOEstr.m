function DOEstr=mkSubFolderFromDOEstr(DOEstr)
    % New Folder  Name & Path
    DOEstr=DOEstr;
    parentPath=DOEstr.path;
    %%
    DesignNumbers=fieldnames(DOEstr);
    for DesignIndex=1:length(DesignNumbers)
    DOEstr.MotFileDirList{DesignIndex}       = fullfile(parentPath, DesignNumbers{DesignIndex});
        CheckDir = isfolder(DOEstr.MotFileDirList{DesignIndex} );
        if CheckDir==0
            mkdir(DOEstr.MotFileDirList{DesignIndex} );
        end
    end
end