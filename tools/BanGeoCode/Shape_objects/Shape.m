classdef Shape < dynamicprops
    %Shape class for feasibily check and dxf export
    
    properties
        description
        poly
        output_string
        region_point        
        shape_area        
        magnet_angle
        layer
        number
        density
        mass
        length
        volume
    end
    

    
    methods
        
        function obj = dec(obj,decimate_ratio)
            % Decimate barrier points because polybuffer adds a lot of points in the corners
            mat=obj.poly.Vertices;            
            obj.poly.Vertices=DecimatePoly2([mat; [mat(1,1) mat(1,2)];],[decimate_ratio/100 2]);            
        end
        
        function obj = lay(obj,layer,number)
            % Set object layer and number
            obj.layer=layer;
            obj.number=number;
        end
        
        function obj = weight(obj,length,density)
            % Set object mass, length, density and volume
            % lenght -> mm
            % density kg/m^3
            % obj.shape_area -> mm^2
                        
            obj.mass=obj.shape_area/1000^2*length/1000*density;
            obj.length=length;
            obj.density=density;
            obj.volume=obj.mass/density;
        end
        
        
        function obj = des(obj,str)
            % Description
            obj.description=str;
        end
        
        function obj = ply(obj,X,Y,sort)
            % Polyshape
            
            if strcmp(sort,'SortV') % sort vertices, works only on convex shapes
                [X,Y]=sort_vertices(X,Y);
            end
            obj.poly=polyshape(X,Y);
            obj.shape_area=area(obj.poly);  % mm^2
        end
        
        function obj = buf(obj,r)
            % Round polyshape corners
            temp1=polybuffer(obj.poly,-r);
            %plot(temp1);
            if area(temp1)==0
                disp('Shape area is zero, buffer radius is too large or shape is too thin');
            end
            temp2=polybuffer(temp1,r);          
            %plot(temp2);            
            obj.poly=temp2;
        end
        
        function obj = ost(obj,str)
            % Output string for region naming in external FEA software
            if ~strcmp(obj.description,"Air") && strcmp(str,'Rotor Pocket')
                obj.output_string=['Rotor Pocket (',convertStringsToChars(obj.description),')'];
            else                
                obj.output_string=str;
            end
        end
        
        function obj = rgn(obj,enable,tau,poleVangle)
            % Get region within polyshape, if shape is Magnet, define
            % magnetization angle
            
            if strcmp(obj.description,"Magnet")
                [X,Y,obj.magnet_angle]=get_magnet_angle(obj.poly,obj.output_string,enable,tau,poleVangle);
            else
                [X,Y]=find_best_region(obj.poly,obj.output_string,enable);
            end
            obj.region_point=[X,Y];
        end
        
        function obj = rot(obj,angle)
            % Rotate rotor to default position
            obj.poly=rotate(obj.poly,-rad2deg(angle),[0,0]);
        end
        
        function obj = rmholes(obj)
            % remove all holes from shapes after construction is finished
            obj.poly=rmholes(obj.poly);
        end
        
        function obj = plot(obj,enable)
            %Matlab color selection tool 
            %uisetcolor
            
            if enable
                
                color_all=...
                    [{"Magnet",         [0.47 0.67 0.16] 	};...
                    {"Air",             [1 1 1]             };...
                    {"Notch",           [1 1 1]             };...
                    {"Epoxy",           [0.98, 0.98, 0.1]   };...
                    {"Duct",            [1 1 1]             };...
                    {"Stator",          [0.9 0.9 0.9]       };...
                    {"Slot region 9",   [0.99 0.34 0.01]    };...
                    {"Slot region 8",   [0.35 0.7 0.93]     };...
                    {"Slot region 7",   [0.99 0.34 0.01]    };...
                    {"Slot region 6",   [0.35 0.7 0.93]     };...
                    {"Slot region 5",   [0.99 0.34 0.01]    };...
                    {"Slot region 4",   [0.35 0.7 0.93]     };...
                    {"Slot region 3",   [0.99 0.34 0.01]    };...
                    {"Slot region 2",   [0.35 0.7 0.93]     };...
                    {"Slot region 1",   [0.99 0.34 0.01]    };...
                    {"Wedge",           [0.65 0.65 0.65]  	};...
                    {"Rotor",           [0.9 0.9 0.9]   	};...
                    {"Shaft",           [0.65 0.65 0.65]  	};...
                    ];
                
                %
                if strcmp(obj.description,"Air") 
                    plot(obj.poly,'FaceAlpha',0);
                else
                    idx=find(contains(string(color_all(:,1)),obj.description));
                    col=cell2mat(color_all(idx,2));
                    plot(obj.poly,'FaceColor',col,'FaceAlpha',0.3);
                end
                hold on
            end
        end
        
        
    end
end

function [x,y]=find_best_region(polyin,name,enable)

%number of mesh rectangles;
N=4;

x_min=min(polyin.Vertices(:,1));
x_max=max(polyin.Vertices(:,1));

y_min=min(polyin.Vertices(:,2));
y_max=max(polyin.Vertices(:,2));


A=x_max-x_min;
B=y_max-y_min;

if A>B
    
    mesh_limits_x=[x_min x_max];
    mesh_limits_y=[y_min y_min+A];
else
    mesh_limits_x=[x_min x_min+B];
    mesh_limits_y=[y_min y_max];
    
end


grid_X=mesh_limits_x(1):(mesh_limits_x(2)-mesh_limits_x(1))/N:mesh_limits_x(2);
grid_Y=mesh_limits_y(1):(mesh_limits_y(2)-mesh_limits_y(1))/N:mesh_limits_y(2);
[X,Y] = meshgrid(grid_X,grid_Y);

k=1;
for i=1:N
    for j=1:N
        polyvec(k)=polyshape([X(i,j) X(i+1,j) X(i+1,j+1) X(i,j+1)],[Y(i,j) Y(i+1,j) Y(i+1,j+1) Y(i,j+1)]);
                  
        hold on
        k=k+1;
    end
    
end
% plot(polyvec,'FaceAlpha',0);
% plot(polyin);
temp=intersect(polyvec,polyin);
poly_area=area(temp);

best_cell=find(poly_area==max(poly_area));
best_cell=best_cell(1);


polyout=intersect(polyvec(best_cell),polyin);

%check if there is extra regions
R1=sortregions(polyout,'area','descend');
R2=regions(R1);
%select biggest region as final area
final=R2(1);

[x,y]=centroid(final);


%if shape is not convex find point inside him
if ~isinterior(final,x,y)
    %plot(final,'FaceColor','r','FaceAlpha',0.1);
    [x,y]=find_best_region(final,name,enable);
else
    if enable
        %plot(final,'FaceColor','b','FaceAlpha',0.1);
        plot(x,y,'*k');
        %set(l, 'Interpreter', 'none')
        text(x+0.5,y,name, 'Interpreter', 'none');
        %set(l, 'Interpreter', 'latex')
    end
end
end

function [X_c,Y_c,magnet_angle]=get_magnet_angle(polyin,name,enable, tau,poleVangle)

[X_c,Y_c]=centroid(polyin); %magnet centroid
[beta_c,R_c]=cart2pol(X_c,Y_c);

gama=pi/2-deg2rad(poleVangle)/2;
beta1=pi/2+tau/2-deg2rad(poleVangle)/2;

if gama==0
 magnet_angle=tau/2;
else
if beta_c < tau/2
    magnet_angle=beta1;
else
    magnet_angle=tau-beta1;
end

end

arrow_length=3;
k=tan(magnet_angle);

if abs(k) > 1e14 %check if k equals zero, important for matlab precision error
    X_v=X_c;
    Y_v=Y_c+arrow_length;
else
    X_v=X_c+arrow_length*cos(magnet_angle);
    Y_v=k*(X_v-X_c)+Y_c;    
end

P1=[X_c,Y_c];
P2=[X_v,Y_v];
D = P2 - P1;

if enable
    plot(X_c,Y_c,'*k');
    text(X_c+0.5,Y_c,name, 'Interpreter', 'none');
    arrows( P1(1), P1(2), D(1), D(2),'Cartesian');
    hold on
end

magnet_angle=rad2deg(magnet_angle);
end