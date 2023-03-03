classdef    DataPkBetaMap < DataMap
    properties
%     magVec  
%     gammaVec
    flux_linkage_map 
    current_dq_map
    LossMap
    end

    methods (Static)
        plot_xpk(obj)
        plot_xbeta(obj,data)
        plot_xdyq(obj,data)
        plot_xpkybeta(obj)
        compMatFile(obj)       
    end
    methods
        obj=compMatFileLoss(obj)
    end
end
