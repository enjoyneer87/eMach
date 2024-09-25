


for figureIndex=1:2:3
mergeFigures([figureIndex figureIndex+4])
    if mod(figureIndex,2)==0
        view(2)
        setlegendBoxShape(2)
    end
    legend
    setlegendBoxShape(5)
    grid on 
    box on
end



mergeFigures([20 6])   % slot 1 Theta TS/ MS
    view(2)
    setlegendBoxShape(2)
    grid on 
    box on
mergeFigures([80 24])   % slot 4 Theta  TS / MS:T 6*SlotIndex
    view(2)
    setlegendBoxShape(2)
    grid on 
    box on


mergeFigures([4 8])      % slot 1 R
    view(2)
    setlegendBoxShape(2)
    grid on 
    box on
    
    
mergeFigures([16 32])
    view(2)
    setlegendBoxShape(2)
    grid on 
    box on
