classdef    data_pk_beta_map
    properties
    flux_linkage
    current
    beta
    current_dq
    voltage
    rpm
    force_map
    torque_map
    Rs
    p
    end

    methods (Static)
        plot_xpk(obj)
        plot_xbeta(obj,data)
        plot_xdyq(obj,data)
    end
end
