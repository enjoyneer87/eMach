classdef Class_Motor
   properties
      Prop
   end
   
   methods
      function obj = Class_Motor(val)
         if nargin > 0
            obj.Prop = val;
         end
      end
   end
end