function autoZlabel(varName)
    if contains(varName,'loss')
        zlabel('loss[W]', 'Interpreter', 'none');
    elseif contains(varName,'Loss')
        zlabel('loss[W]', 'Interpreter', 'none');
    elseif contains(varName,'Flux')
        zlabel('[Vs]', 'Interpreter', 'none');
    elseif contains(varName,'Current')
        zlabel('[A]', 'Interpreter', 'none');
    else
        zlabel('Value', 'Interpreter', 'none');
    end
    
end