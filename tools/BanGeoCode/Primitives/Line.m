classdef Line < dynamicprops & matlab.mixin.Copyable
    %Line definition class
    
    properties 
        P1 %starting point
        P2 %end point       
        name
        x
        y
        enable_plot
        length
             
    end
    

    
    methods
        
        function obj = def(obj,P1,P2)
            %P1 -> starting point
            %P2 -> end point
            
            obj.P1=copyElement(P1);
            obj.P2=copyElement(P2);
            obj.length=sqrt((obj.P1.x-obj.P2.x).^2+(obj.P1.y-obj.P2.y).^2);
            
            N=100;
            for i=1:numel(obj.P1.x)
                obj.x(i,:)=linspace(obj.P1.x(i),obj.P2.x(i),N);
                obj.y(i,:)=linspace(obj.P1.y(i),obj.P2.y(i),N);
            end
          
        end
        
        function obj = rot(obj,angle)
            %rotate line points by angle                     
            obj.P1=obj.P1.rot(angle);
            obj.P2=obj.P2.rot(angle);   
            obj = def(obj,obj.P1,obj.P2);
        end
        
        function obj = flip(obj)
            %flip start and end points
            temp=obj.P1;      
            obj.P1=obj.P2;
            obj.P2=temp;          
        end
        
       
        function obj = mrr(obj,angle)
            %mirror points by angle             
            obj.P1=obj.P1.mrr(angle);
            obj.P2=obj.P2.mrr(angle);
           
        end
        
        function obj = plot(obj,enable)
            obj.enable_plot=enable;
            if obj.enable_plot
                obj.name = inputname(1);
                for i=1:numel(obj.P1.x)
                    plot([obj.P1.x(i) obj.P2.x(i)],[obj.P1.y(i) obj.P2.y(i)]);
                    
                    p1=[obj.P1.x(i),obj.P1.y(i)];
                    p2=[obj.P2.x(i),obj.P2.y(i)];
                    D = p2 - p1;
                    SHAPE = 0.2*[0.2,0.2,0.15,0.05];
                    arrows( p1(1), p1(2), D(1), D(2),SHAPE,'Cartesian','Cartesian','FaceColor',rand(3,1));
                
                    hold on
                end
            end
        end
        
    end
    
    methods(Access = protected)
        % Override copyElement method:
        function cpObj = copyElement(obj)
            % Make a shallow copy of all four properties
            cpObj = copyElement@matlab.mixin.Copyable(obj);
            % Make a deep copy of the object
            cpObj.P1 = copy(obj.P1);
            cpObj.P2 = copy(obj.P2);
        end
    end
    
end



