function multiMotorCAD(n)
    for i = 1:n
        app{i} = actxserver('MotorCAD.AppAutomation');
    end
end