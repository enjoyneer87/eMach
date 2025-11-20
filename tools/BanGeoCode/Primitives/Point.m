classdef Point < dynamicprops & matlab.mixin.Copyable
    %Point definition class, all angles should be entered in radians
    
    properties 
        beta
        R
        x
        y
        name
        enable_plot
    end
    

    
    methods
        
        function obj = c2p(obj)   % cartesian to polar
            [obj.beta,obj.R]=cart2pol(obj.x,obj.y);
        end
        
        function obj = p2c(obj)   % polar to cartesian
            [obj.x,obj.y]=pol2cart(obj.beta,obj.R);
            
            if obj.beta == pi/2 %fix for pol2cart error
                obj.x=0;
            end
        end
        
        function obj = yb2xR(obj)
            obj.x = obj.y./tan(obj.beta);
            obj.R = sqrt(obj.x.^2+obj.y.^2);
        end
        
        function obj = xb2yR(obj)
            obj.y = obj.x/tan(obj.beta);
            obj.R = sqrt(obj.x.^2+obj.y.^2);
        end
        
        function obj = rot(obj,angle)
            obj.beta = obj.beta+angle;
            obj.R = obj.R;            
            obj.p2c;
           
        end
        
        function obj = mrr(obj,angle)
            %mirror points around line under angle
            m=tan(angle);
            symmetry_matrix=(1/(1+m^2))*[1-m^2	2*m;
                                        2*m    m^2-1;];
             A=symmetry_matrix*[obj.x', obj.y']';
    
            obj.x=A(1,:);
            obj.y=A(2,:);            
            obj.c2p;            
        end
        
        function obj = xR2yb(obj)
            obj.y = sqrt(obj.R.^2-obj.x.^2);
            obj.beta = atan(obj.y./obj.x);
        end
        
        function obj = reset(obj,T,idx)
            obj.x(idx) = T.x(idx);
            obj.y(idx) = T.y(idx);
            obj.R(idx) = T.R(idx);
            obj.beta(idx)=T.beta(idx); 
        end
        
        function obj = plot(obj,enable)
            obj.enable_plot=enable;
            if obj.enable_plot
                obj.name = inputname(1);
                plot(obj.x,obj.y,'o');
                text(obj.x,obj.y,obj.name);
                hold on
            end
        end        

    end
end

