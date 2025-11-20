function desc = getTableDescOrDefault(S, fieldname)
    if isfield(S, fieldname) && isprop(S.(fieldname), 'Properties') && isprop(S.(fieldname).Properties, 'Description')
        desc = S.(fieldname).Properties.Description;
    else
        desc = ['No ', fieldname];
    end
end
