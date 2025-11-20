
function deltaZ = computeDeltaZ(z_static_func, IdqList, z_dyn_measured)
    Id = IdqList(:,1);
    Iq = IdqList(:,2);
    z_static = z_static_func(Id, Iq);
    deltaZ = z_dyn_measured - z_static;
end
