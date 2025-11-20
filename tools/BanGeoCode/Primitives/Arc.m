classdef Arc < dynamicprops & matlab.mixin.Copyable
    % Arc definion class
    % If C1 == C2
    %   Arc is reduced to same points Or = C1, C2 = C1
    %   x = y = [C1.x , C1.x ... ] in length Np
    % x,y are vertex vectors for polyshape feasibility check
    % sweep angle must be > 0 and < pi, otherwise bugs may occur, use
    % circle Arc_CC if this functionaluty is needed
    
    
    properties 
        %arc origin
         Or
        %arc start Point
         C1       
        %arc end Point
         C2
        %arc coordinates for feasibility check
        x
        y
        name
        enable_plot             
        
        r       %arc radius
        beta_1  %start angle
        beta_2  %end_angle
    end
    

    
    methods
        
        function obj = def(obj,C1,C2,Or)
            %C1 -> starting point
            %C2 -> end point
            %Or -> arc origin Orint
            %if Or is [], that means arc origin is 0,0
            
            if isempty(Or)
                Or=Point();
                Or.x=zeros(1,numel(C1.x));
                Or.y=zeros(1,numel(C1.x));
                Or.c2p;
            end
            
            obj.Or=copyElement(Or);
            obj.C1=copyElement(C1);
            obj.C2=copyElement(C2);
            
%             obj.C1.plot(true);
%             obj.C2.plot(true);
%             obj.Or.plot(true);
            
            startAngle = wrapTo2Pi(atan2((C1.y-Or.y),(C1.x-Or.x)));
            endAngle =   wrapTo2Pi(atan2((C2.y-Or.y),(C2.x-Or.x)));
            
            sweepAngle = endAngle - startAngle;
            idx=find(sweepAngle < 0);
            
            if ~isempty(idx)
                sweepAngle(idx) = - sweepAngle(idx);  
                
                %if sweepAngle(idx) ~= pi
                startAngle(idx) = endAngle(idx);
                %end
            end            

            idx=find(sweepAngle > pi);
            if ~isempty(idx)
                sweepAngle(idx) = sweepAngle(idx)-2*pi;
            end
            
   
            temp.beta_1=startAngle;
            temp.beta_2=startAngle+sweepAngle;
            
            % sort angles for correct plotting
            for i=1:numel(temp.beta_1)
                angles      =[temp.beta_1(i),temp.beta_2(i)];
                obj.beta_1(i)  =min(angles);
                obj.beta_2(i)  =max(angles);
            end


            Np=100;
            %create arc
            for i=1:numel(obj.beta_1)
                
                flag3=abs(C1.y(i)-C2.y(i)) < 1e4*eps(min(abs(C1.y(i)),abs(C2.y(i))));
                flag4=abs(C1.x(i)-C2.x(i)) < 1e4*eps(min(abs(C1.x(i)),abs(C2.x(i))));
                
                flag=(flag3 && flag4);
                
                if flag % reduce arc to points three same points
                    theta =linspace(obj.beta_1(i),obj.beta_1(i),Np);
                    obj.Or.reset(C1,i);
                    obj.C2.reset(C1,i);
                    obj.beta_2(i)=obj.beta_1(i);
                else
                    %theta=linspace(obj.beta_1(i),obj.beta_2(i),Np); 
                     theta = get_theta(obj.beta_1(i),obj.beta_2(i),sweepAngle(i),Np);
                end
                
                obj.r(i)=sqrt((obj.C1.y(i)-obj.Or.y(i)).^2+ (obj.C1.x(i)-obj.Or.x(i)).^2);
               
                A=Or.x(i)+obj.r(i)*cos(theta)';
                B=Or.y(i)+obj.r(i)*sin(theta)';
                
                %if issorted(A) %if vector is not ascending flip it
                
                flag1=abs(A(1)-C1.x(i)) < 1e4*eps(min(abs(A(1)),abs(C1.x(i))));
                flag2=abs(B(1)-C1.y(i)) < 1e4*eps(min(abs(B(1)),abs(C1.y(i))));
                if flag1 && flag2 %if vector is not starting with C1
                    obj.x(i,:)=A';
                    obj.y(i,:)=B';
                else
                    obj.x(i,:)=fliplr(A');
                    obj.y(i,:)=fliplr(B');
                end
                

                
            end
            
                
        end
            
     
       function obj = flip(obj)
            %flip all object properties
            temp=obj.C1;
            obj.C1=obj.C2;
            obj.C2=temp;
            obj = obj.def(obj.C1,obj.C2,obj.Or);
       end

        
             function obj = mrr(obj,angle)
            %mirror points by angle in positive direction
            
            obj.C1=obj.C1.mrr(angle);
            obj.C2=obj.C2.mrr(angle);
            obj.Or=obj.Or.mrr(angle);
            
            X=obj.x;
            Y=obj.y;
            obj = obj.def(obj.C1,obj.C2,obj.Or);
            
            for i=1:numel(obj.beta_1)
                m=tan(angle);
                symmetry_matrix=(1/(1+m^2))*[1-m^2	2*m;
                    2*m    m^2-1;];
                A=symmetry_matrix*[X(i,:); Y(i,:)];
                
                X1(i,:)=A(1,:);
                Y1(i,:)=A(2,:);
 %               
 %               plot(X1(i,:),Y1(i,:),'r')
            end
    
            obj.x=X1;
            obj.y=Y1;
            
            
%            
            %obj=mrr_vec(obj,angle); %set x,y coordinates for plotting
        end
        
        function obj = rot(obj,angle)
            %rotate points by angle   
            
            for i=1:numel(obj.beta_1)
                
                rotor_matrix=[  cos(angle) -sin(angle);
                                sin(angle) cos(angle);];                
                %rotacija
                A=rotor_matrix*[obj.x(i,:); obj.y(i,:)];
                obj.x(i,:)=A(1,:);
                obj.y(i,:)=A(2,:);                
            end
            
            obj.beta_1= obj.beta_1+ angle;     
            obj.beta_2= obj.beta_2+ angle; 
            obj.C1=obj.C1.rot(angle);
            obj.C2=obj.C2.rot(angle);
            obj.Or=obj.Or.rot(angle);
%             obj = obj.def(obj.C1,obj.C2,obj.Or);
        end
        
        function obj = plot(obj,enable)
            obj.enable_plot=enable;
            if obj.enable_plot && ~isempty(obj.x) 
                daspect([1 1 1]);
                obj.name = inputname(1);
                plot(obj.x',obj.y');
                text(obj.x(round(end/2)),obj.y(round(end/2)),obj.name);
                [n,m]=size(obj.x);
                for i=1:n
                    
                    P1=[obj.x(i,m/2-3),obj.y(i,m/2-3)];
                    P2=[obj.x(i,m/2+3),obj.y(i,m/2+3)];
                    D = P2 - P1;                                        
                    SHAPE = [1,1,0.75,0];
                    arrows( P1(1), P1(2), D(1), D(2),SHAPE,'Cartesian','FaceColor',rand(3,1));
                end
                
                hold on
            else
                %the arc does not exist
            end
        end        

    end
    
    methods(Access = protected)
        % Override copyElement method:
        function cpObj = copyElement(obj)
            % Make a shallow copy of all four properties
            cpObj = copyElement@matlab.mixin.Copyable(obj);
            % Make a deep copy of the object
            cpObj.C1 = copy(obj.C1);
            cpObj.C2 = copy(obj.C2);
            cpObj.Or = copy(obj.Or);
        end
    end
    
end

function theta = get_theta(beta_1,beta_2,sweepIn,Np)

sweepAngle=abs(sweepIn);

if (beta_2 > beta_1) && (beta_1 + sweepAngle <= 2*pi)
    theta=linspace(beta_1,beta_2,Np);
end

if (beta_2 < beta_1)
    if (beta_1 + sweepAngle < 2*pi)
        theta=linspace(beta_1,beta_2,Np);
    end
    
    if (beta_1 + sweepAngle >= 2*pi)
        theta=[linspace(beta_1,2*pi,Np/2) ,linspace(0,beta_2,Np/2)];
    end
    
    if (beta_1 + sweepAngle > beta_2)
        theta=[linspace(beta_1,2*pi,Np/2) ,linspace(0,beta_2,Np/2)];
    end
end

if beta_2 == 0
    
    if(beta_1 + sweepAngle < 2*pi)
        theta=linspace(beta_1,2*pi,Np);
    end
    if (beta_1 + sweepAngle == 0)
        theta=linspace(beta_1,0,Np);
    end
    
end

end
