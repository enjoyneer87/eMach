function len = lineLength(line)
    % Calculate the length of a line
    len = sqrt((line(2,1) - line(1,1))^2 + (line(2,2) - line(1,2))^2);
end
