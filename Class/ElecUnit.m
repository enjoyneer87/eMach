classdef ElecUnit
    properties
        myValue
        myUnit
    end
    methods
        function obj = myData(value, unit)
            obj.myValue = value;
            obj.myUnit = unit;
        end
    end
end
