function val = getFieldOrDefault(S, fieldname, default)
    if isfield(S, fieldname)
        val = S.(fieldname);
    else
        val = default;
    end
end