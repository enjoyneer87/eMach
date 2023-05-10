% Add this function at the end of your script
function adjustedText(x, y, name, xTime, varData)
    x_adj = x;
    y_adj = y;
    margin = 0.5;
    overlaps = true;

    while overlaps
        overlaps = false;
        for k = 1:length(varData)
            var = varData{k};
            if abs(x_adj - var(1)) < margin && abs(y_adj - var(2)) < margin
                overlaps = true;
                y_adj = y_adj - margin;
                break;
            end
        end
    end
    varData{end+1} = [x_adj, y_adj];
    text(x_adj, y_adj, name, 'HorizontalAlignment', 'right', 'VerticalAlignment', 'middle');
end