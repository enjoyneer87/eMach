function qs=calcWindingQs(NumberofSlots,NumberofPole,varargin)
if nargin>3
NumberPhase=varargin;
else
NumberPhase=3;
end
%% 극당상당 슬롯수
    qs=NumberofSlots/NumberofPole/NumberPhase;
end
