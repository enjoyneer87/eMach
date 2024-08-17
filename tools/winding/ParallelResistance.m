function resistanceAll= ParallelResistance(varargin) 

resistanceAll=0; 

for n=1:length(varargin)
    rtemp = varargin{n}; 
    resistanceAll = resistanceAll + 1/rtemp; 

end 
resistanceAll = 1/resistanceAll;