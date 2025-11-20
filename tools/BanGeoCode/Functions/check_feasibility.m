function flag = check_feasibility(Shape,angle,DstChk)
%This function checks if any of the shapes are overlapping. Shape is a
%vector of shapes and angle is the symmetriy angle of pole or slot.
%If flag=true, geometry is feasible


%% Check general feasibility

for i=1:numel(Shape)
    
    flag3(i)=false;
    
    %skip the final lamminate, otherwise it can be false overlaps
    if ~strcmp(Shape(i).description,'Rotor')
        
        polyvec(i)=Shape(i).poly;
        %check region number, if > 1 shape is pertruded other shape, i.e. magnet clashes with airpocket
        region_no(i)=polyvec(i).NumRegions;
        
        if region_no(i) >1
            plot(polyvec(i));
            polyout = regions(polyvec(i));
            for j=1:numel(polyout)
                
                plot(polyout(j),'FaceColor','red','FaceAlpha',0.5);
                hold on
            end
        end
        
        X=Shape(i).poly.Vertices(:,1);
        Y=Shape(i).poly.Vertices(:,2);
        
        [beta,R] = cart2pol(X,Y);
        
        if any(beta > (angle+2.5*eps))|| any((beta+2.5*eps)< 0)
            flag3(i)=true;
            plot(polyvec(i),'FaceColor','red','FaceAlpha',0.5);
            disp('Point beyond symmetry line');
        end
    end
    
end

%if any of the coordinates is clashing the symmetry line flag4 is false
flag4=~any(flag3);

%detect if barriers overlap
detect_overlapping = overlaps(polyvec);
%detect_overlapping

%if detect_overlap is not unitary matrix there are some overlapping, proceed to minimization
flag1=(isequal(detect_overlapping, eye(size(detect_overlapping, 1)) ));
flag2=all( region_no < 2);

% plot intersecting shapes
mask=detect_overlapping.*~eye(size(detect_overlapping, 1));
idx=find(mask>0);
[row ~] =find(mask>0);
plot(polyvec(row),'FaceColor','red','FaceAlpha',0.5);

%% Check that minimal distance is bigger than buffer between components in the list
%if this step is irrelevant put buffer column to 0
if DstChk
    
    list=["Epoxy"   0.25;...
        %"Duct"    0;...
        %"Notch"   0;...
        %"Shaft"   2;...
        ];
    
    j=1;
    for i=1:numel(Shape)
        %skip all elements which are not defined in the list
        if any(strcmp(Shape(i).description,list(:,1)))
            iRow = find(strcmp(list(:,1), Shape(i).description)==1);
            buffer=str2num(list(iRow,2));
            
            polyvec_2(j)=Shape(i).poly;
            polyvec_2(j)=polybuffer(polyvec_2(j),buffer);%make shapes bigger by buffer to avoid too narrow geometry
            plot(polyvec_2(j),'EdgeColor','red','FaceAlpha',0);
            j=j+1;
        end
        
    end
    
    if exist('polyvec_2','var')
        detect_overlapping_2 = overlaps(polyvec_2);
        %if detect_overlap is not unitary matrix there are some overlapping, proceed to minimization
        flag5=(isequal(detect_overlapping_2, eye(size(detect_overlapping_2, 1)) ));        
        if ~flag5
            cprintf('red','Distance between shape borders is less than required \n');
        end        
    else
        flag5=true;
    end
    
else    
    flag5=true;
end

%% Final flag check

flag=flag1 && flag2 && flag4 && flag5;
% if flag
%     disp('Feasible geometry!');
% else
%     disp('Infeasible geometry');
% end





end

