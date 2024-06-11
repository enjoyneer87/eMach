function entities = readDXF(filename)
% based on Read DXF File data by Sebastian, 
% https://se.mathworks.com/matlabcentral/fileexchange/24572-read-dxf-file-data
%
% POLYLINES:
%   8:  Layer no.
%  10:  X value; APP: 2D point Vertex coordinates (in OCS), multiple entries; one entry for each vertex
%  20:  Y value of vertex coordinates (in OCS), multiple entries; one entry for each vertex
%  70:  Polyline flag (bit-coded); default is 0, 1 = Closed, 128 = Plinegen
%  42:  c (optional; default is 0). 
%       The bulge is the tangent of one fourth the included angle for an arc segment, 
%       made negative if the arc goes clockwise from the start point to the endpoint. 
%       A bulge of 0 indicates a straight segment, and a bulge of 1 is a semicircle.
%       See http://www.afralisp.net/archive/lisp/Bulges1.htm
%       and John Hughes, https://math.stackexchange.com/questions/482751/how-do-i-move-through-an-arc-between-two-specific-points
%
% ELLIPSE:
% 100:  Subclass marker (AcDbEllipse)
%  10:  Center point (in WCS) DXF: X value; APP: 3D point
%  20:  DXF: Y and Z values of center point (in WCS)
%  11:  Endpoint of major axis, relative to the center (in WCS) DXF: X value; APP: 3D point
%  21:  DXF: Y and Z values of endpoint of major axis, relative to the center (in WCS)
%  40:  Ratio of minor axis to major axis
%  41:  Start parameter (this value is 0.0 for a full ellipse)
%  42:  End parameter (this value is 2pi for a full ellipse)


    % Read file
    fid = fopen(filename);    
    AllValues = textscan(fid,'%d%s','Delimiter','\n');
    fclose(fid);
    
    AllCodes  = AllValues{1}; % Code group numbers
    AllValues = AllValues{2}; % Values
    
    % Extract entities
    EntPos = find(AllCodes==0);
    
    % Entities Position
    nEntities   = find(strcmp('ENTITIES',AllValues(EntPos(1:end-1)+1)));
    mEntities   = find(strcmp('ENDSEC'  ,AllValues(EntPos(nEntities:end))));
    EntPos      = EntPos(nEntities:nEntities-1+mEntities(1));
 
    
    % get relevant data for each entity
    for i = 1:length(EntPos)-2
        
        % current entity codes/values
        eCodes     = AllCodes(EntPos(i+1):EntPos(i+2)-1);
        eStrings   = AllValues(EntPos(i+1):EntPos(i+2)-1);
        eValues    = str2double(eStrings);
        
        entities(i).name        = AllValues{EntPos(i+1)};
        entities(i).layer       = eStrings{eCodes==8};
        try
            entities(i).linetype    = eStrings{eCodes==6};
        catch
            entities(i).linetype    = '';
        end
        
			% get color
        color = get_values(62,eCodes,eValues);
        if isempty(color)
            entities(i).color = 0;
        else
            entities(i).color = color;
        end
        
        switch upper(entities(i).name)
            case 'HATCH'
                % just store it for coloring previous entity.
                
            case 'SPLINE'
                entities(i).spline.degree     = get_values(71,eCodes,eValues);
                entities(i).spline.no_knots   = get_values(72,eCodes,eValues);
                entities(i).spline.no_control = get_values(73,eCodes,eValues);
                entities(i).spline.knot_value = get_values(40,eCodes,eValues);
                entities(i).spline.X          = get_values(10,eCodes,eValues);
                entities(i).spline.Y          = get_values(20,eCodes,eValues);
                
            case 'LINE' 
                % (Xi,Yi,Xj,Yj) start and end points
                entities(i).line = [get_values(10,eCodes,eValues),...
                                    get_values(20,eCodes,eValues),...
                                    get_values(11,eCodes,eValues),...
                                    get_values(21,eCodes,eValues)];
                
            case 'LWPOLYLINE' 
                % (X,Y) coordinates of vertices + bulges
                ix = eCodes == 10;
                iy = eCodes == 20;
                ib = eCodes == 42;
                i_poly = ix + iy + ib;
                
                % closed polygon
                entities(i).closed = get_values(70,eCodes,eValues);
                
                eCodes(~i_poly)=[];
                eValues(~i_poly)=[];
                
                n_verts = sum(ix) + sum(ib);
                verts = zeros(n_verts,2);
                iv = 0;
                for j=1:length(eCodes)
                    switch eCodes(j)
                        case 10
                            iv = iv + 1;
                            verts(iv,1) = eValues(j);
                        case 20
                            verts(iv,2) = eValues(j);
                        case 42
                            iv = iv + 1;
                            verts(iv,1) = NaN; % handle bulges later
                            verts(iv,2) = eValues(j);
                    end
                end
                
                % handle bulges
                ib = find(isnan(verts(:,1)));
                for j = length(ib):-1:1
                    P1 = verts(ib(j)-1,:)';
                    
                    if ib(j)+1 > size(verts,1)
                        P2 = verts(1,:)';
                    else
                        P2 = verts(ib(j)+1,:)';
                    end 
                    b  = verts(ib(j),2);
                    
                    bulge_verts = bulge(P1,P2,b,15);
                    
                    % glue vertices array together including discretized arcs
                    verts = [verts(1:ib(j)-1,:);
                             bulge_verts;
                             verts(ib(j)+1:end,:)];
                end
                
                % return polygon vertices
                entities(i).poly = verts;               
               
            case 'CIRCLE' 
                % (X Center,Y Center,Radius)
                entities(i).circle = [get_values(10,eCodes,eValues),...
                                      get_values(20,eCodes,eValues),...
                                      get_values(40,eCodes,eValues)];
                
            case 'ARC' 
                % (X Center,Y Center,Radius,Start angle,End angle)
                entities(i).arc = [get_values(10,eCodes,eValues),...
                                   get_values(20,eCodes,eValues),...
                                   get_values(40,eCodes,eValues),...
                                   get_values(50,eCodes,eValues),...
                                   get_values(51,eCodes,eValues)];
                
            case 'POINT' 
                % (X,Y) Position
                entities(i).point = [get_values(10,eCodes,eValues),...
                                     get_values(20,eCodes,eValues)]; %#ok<*AGROW>
            
            case 'ELLIPSE' 
                % X center ,Y center, X end, Y end, ratio, start, end
                entities(i).ellipse = [get_values(10,eCodes,eValues),...
                                       get_values(20,eCodes,eValues),...
                                       get_values(11,eCodes,eValues),...
                                       get_values(21,eCodes,eValues),...
                                       get_values(40,eCodes,eValues),...
                                       get_values(41,eCodes,eValues),...
                                       get_values(42,eCodes,eValues)];
                
                if entities(i).ellipse(6)==0 && entities(i).ellipse(7)>0.999*2*pi
                    entities(i).closed = 1;
                else
                    entities(i).closed = 0;
                end
        
        end        
    end      

end