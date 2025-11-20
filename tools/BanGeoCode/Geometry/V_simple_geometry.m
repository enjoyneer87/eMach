

lay=        in.VMagnet_Layers;
poleVangle= in.PoleVAngle_Array(1:lay);
poles=      in.Pole_Number;
Rsh=        in.Shaft_Dia/2;
Db=         in.Stator_Bore;
da=         in.Airgap;
Dsh_hole=   in.Shaft_Hole_Diameter;
Rr=         0.5* Db-da;
Ds=         in.Stator_Lam_Dia;

Ns=         in.Slot_Number;

h_mag=      in.MagnetThickness_Array(1:lay);
h_c_out=    in.VShape_Magnet_ClearanceOuter(1:lay);
h_c_in=     in.VShape_Magnet_ClearanceInner(1:lay);
h_c=        h_c_out+h_c_in;
h=          h_mag + h_c;

w=          in.MagnetBarWidth_Array(1:lay);
V=          in.VSimpleWidth_Array(1:lay);

ext_i=      in.VSimpleEndRegion_Inner_Array(1:lay);
ext_o=      in.VSimpleEndRegion_Outer_Array(1:lay);

sh=         in.VSimpleMagShift_Array(1:lay);
b=          in.BridgeThickness_Array(1:lay);
p=          in.VSimpleMagnetPost_Array(1:lay);


nd=     in.PoleNotchDepth;
ndo=    in.PoleNotchArc_Outer;
ndi=    in.PoleNotchArc_Inner;

betamin=90-180/poles;
gamma=90-poleVangle/2;
tau_pole=2*pi/poles;

r_10=in.r_10;
r_11=in.r_11;
r_M=in.r_M;



for i=1:lay
    if ext_i(i)==0
        Ri(i)=0;
    else
        Ri(i)=(ext_i(i)^2+(0.5*h(i))^2)/(2*ext_i(i));
    end
    
    if ext_o(i)==0
        Ro(i)=0;
    else
        Ro(i)=(ext_o(i)^2+(0.5*h(i))^2)/(2*ext_o(i));
    end
    
end


%% Point r0 def
P_r0=Point();
P_r0.x=0;
P_r0.y=0;
P_r0.c2p;
P_r0.plot(rotor_construction);

%Point B %centerpoint of inner barrier arc
P_rB=Point();
P_rB.x=Ri+0.5*p;


%Point A
P_rA=Point(); %centerpoint of inner barrier edge
P_rA.x=P_rB.x-(Ri-ext_i).*cos(deg2rad(gamma));


%Point 1
P_r1=Point();
P_r1.x=P_rA.x-0.5*h.*cos(deg2rad(poleVangle/2));
for i=1:lay
    if P_r1.x(i)<=0.5*p(i) %recalculation of the points
        P_r1.x(i)=0.5*p(i);
        P_rA.x(i)=P_r1.x(i)+0.5*h(i).*cos(deg2rad(poleVangle(i)/2));
    end
end


%Point C
P_rC=Point();
P_rC.x=P_rA.x+V.*cos(deg2rad(gamma));


%Point D
P_rD=Point(); %centerpoint of outer barrier arc
P_rD.x=P_rC.x-(Ro-ext_o).*cos(deg2rad(gamma));
P_rD.R=Rr-b-Ro;
P_rD.y = sqrt(P_rD.R.^2-P_rD.x.^2);
P_rD.c2p;

P_rC.y=P_rD.y+(Ro-ext_o).*sin(deg2rad(gamma));
P_rC.c2p();

%%Point E
%PE=Point(); %touching point of two circles
%PE.R=Rr-b
%PE.beta=PD.beta

%Point 4
P_r4=Point();
P_r4.y=P_rC.y+0.5*h.*cos(deg2rad(gamma));
P_r4.x=P_r1.x+V.*cos(deg2rad(gamma));
P_r4.c2p();

for i=1:lay
    if P_rD.beta(i)>P_r4.beta(i) %recalculation of the points if point D has larger angle than point 4
        P_r4.R(i)=Rr-b(i);
        P_r4.y = sqrt(P_r4.R.^2-P_r4.x.^2);
        P_r4.c2p;
        P_rC.y(i)=P_r4.y(i)-0.5*h(i).*cos(deg2rad(gamma(i)));
        P_rD.y(i) = P_rC.y(i) - (Ro(i)-ext_o(i)).*sin(deg2rad(gamma(i)));
    end
end

P_rC.c2p();
P_rD.c2p();
P_rC.plot(rotor_construction);
P_rD.plot(rotor_construction);

P_rA.y=P_rC.y-V.*sin(deg2rad(gamma));
P_rA.c2p();
P_rA.plot(rotor_construction);

P_rB.y=(P_rB.x-P_rA.x).*tan(deg2rad(gamma))+P_rA.y;
P_rB.c2p();
P_rB.plot(rotor_construction);

P_r1.y=P_r4.y-V.*sin(deg2rad(gamma));
P_r1.c2p();
P_r1.plot(rotor_construction);

%Point 2
P_r2=Point();
P_r2.x=P_r1.x+(V/2-w/2+sh).*cos(deg2rad(gamma));
P_r2.y=P_r1.y+(V/2-w/2+sh).*sin(deg2rad(gamma));
P_r2.c2p();
P_r2.plot(rotor_construction);

%Point 3
P_r3=Point();
P_r3.x=P_r2.x+w.*cos(deg2rad(gamma));
P_r3.y=P_r2.y+w.*sin(deg2rad(gamma));
P_r3.c2p();
P_r3.plot(rotor_construction);

%Point 8
P_r8=Point();
P_r8.x=P_r1.x+h.*cos(deg2rad(poleVangle/2));
P_r8.y=P_r1.y-h.*sin(deg2rad(poleVangle/2));
P_r8.c2p();
P_r8.plot(rotor_construction);

%Point 7
P_r7=Point();
P_r7.x=P_r8.x+(P_r2.x-P_r1.x);
P_r7.y=P_r8.y+(P_r2.y-P_r1.y);
P_r7.c2p();
P_r7.plot(rotor_construction);

%Point 6
P_r6=Point();
P_r6.x=P_r8.x+(P_r3.x-P_r1.x);
P_r6.y=P_r8.y+(P_r3.y-P_r1.y);
P_r6.c2p();
P_r6.plot(rotor_construction);

%Point 5
P_r5=Point();
P_r5.x=P_r8.x+(P_r4.x-P_r1.x);
P_r5.y=P_r8.y+(P_r4.y-P_r1.y);
P_r5.c2p();
P_r5.plot(rotor_construction);

%% Notch definition

% Point r10 def
P_r10=Point();
P_r10.R=Rr;
P_r10.beta=deg2rad(betamin+ndo/poles);
P_r10.p2c;
P_r10.plot(rotor_construction);

% Point r11 def
P_r11=Point();
P_r11.R=Rr-nd;
P_r11.beta=deg2rad(betamin+ndi/poles);
P_r11.p2c;
P_r11.plot(rotor_construction);

% Point r12 def
P_r12=Point();
P_r12.R=Rr-nd;
P_r12.beta=deg2rad(betamin);
P_r12.p2c;
P_r12.plot(rotor_construction);

%% Rotor and shaft points

% Point r13 def
P_r13=Point();
P_r13.R=Rsh;
P_r13.beta=pi/2-tau_pole/2;
P_r13.p2c;
P_r13.plot(rotor_construction);

% Point r14 def
P_r14=Point();
P_r14.R=Rsh;
P_r14.beta=pi/2+tau_pole/2;
P_r14.p2c;
P_r14.plot(rotor_construction);

% Point r15 def
P_r15=Point();
P_r15.R=Db/2-da;
P_r15.beta=pi/2-tau_pole/2;
P_r15.p2c;
P_r15.plot(rotor_construction);

% Point r16 def
P_r16=Point();
P_r16.R=Db/2-da;
P_r16.beta=pi/2;
P_r16.p2c;
P_r16.plot(rotor_construction);

% Point r17 def
P_r17=Point();
P_r17.R=Dsh_hole/2;
P_r17.beta=pi/2-tau_pole/2;
P_r17.p2c;
P_r17.plot(rotor_construction);

% Point r18 def
P_r18=Point();
P_r18.R=Dsh_hole/2;
P_r18.beta=pi/2+tau_pole/2;
P_r18.p2c;
P_r18.plot(rotor_construction);


%% Define arcs and lines

% Arc between points P_r1-P_r8, with origin at P_rA
%drw.A_rA = Arc_CC();
drw.A_rA = Arc();
drw.A_rA.def(P_r1,P_r8,P_rB);
drw.A_rA.plot(rotor_construction);

% Arc between points P_r5-P_r4, with origin at P_rC
%drw.A_rC = Arc_CC();
drw.A_rC = Arc;
drw.A_rC.def(P_r5,P_r4,P_rD);
drw.A_rC.plot(rotor_construction);


% Line P4 - P1
drw.L_r01_04=Line();
drw.L_r01_04.def(P_r4,P_r1);
drw.L_r01_04.plot(rotor_construction);

% Line P8 - P5
drw.L_r08_05=Line();
drw.L_r08_05.def(P_r8,P_r5);
drw.L_r08_05.plot(rotor_construction);

%% Magnets

% Arc between points P3-P2-P7
drw.A_r02M = fillet_L2L(P_r3,P_r2,P_r7,r_M,rotor_construction);
drw.A_r02M.plot(rotor_construction);

% Arc between points P6-P3-P2
drw.A_r03M = fillet_L2L(P_r6,P_r3,P_r2,r_M,rotor_construction);
drw.A_r03M.plot(rotor_construction);

% Arc between points P2-P7-P6
drw.A_r07M = fillet_L2L(P_r2,P_r7,P_r6,r_M,rotor_construction);
drw.A_r07M.plot(rotor_construction);

% Arc between points P7-P6-P3
drw.A_r06M = fillet_L2L(P_r7,P_r6,P_r3,r_M,rotor_construction);
drw.A_r06M.plot(rotor_construction);


%Line P3 - P2
drw.L_r03M_02M=Line();
drw.L_r03M_02M.def(drw.A_r03M.C2,drw.A_r02M.C1);
drw.L_r03M_02M.plot(rotor_construction);

%Line P2 - P7
drw.L_r02M_07M=Line();
drw.L_r02M_07M.def(drw.A_r02M.C2,drw.A_r07M.C1);
drw.L_r02M_07M.plot(rotor_construction);

%Line P7 - P6
drw.L_r07M_06M=Line();
drw.L_r07M_06M.def(drw.A_r07M.C2,drw.A_r06M.C1);
drw.L_r07M_06M.plot(rotor_construction);

%Line P6 - P3
drw.L_r06M_03M=Line();
drw.L_r06M_03M.def(drw.A_r06M.C2,drw.A_r03M.C1);
drw.L_r06M_03M.plot(rotor_construction);

%% Notch and rotor

if nd > 0 % notch exists
    
    %Arc P12 - P11
    drw.A_r12_11=Arc();
    drw.A_r12_11.def(P_r12,P_r11,[]);
    drw.A_r12_11.plot(rotor_construction);
    
    %  Arc fillet between lines intersectiong at point P11, with origin at 0,0
    drw.A_r11 = fillet_A2L(P_r10,P_r11,P_r12,[],r_11,rotor_construction);
    drw.A_r11.plot(rotor_construction);
    
    %Redefine Arc P12 - P11 according to A_r11
    drw.A_r12_11=Arc();
    drw.A_r12_11.def(P_r12,drw.A_r11.C1,[]);
    drw.A_r12_11.plot(rotor_construction);
    
    % Arc fillet between lines intersectiong at point P10, with origin at 0,0
    drw.A_r10 = fillet_A2L(drw.A_r11.C2,P_r10,P_r16,[],r_10,rotor_construction);
    drw.A_r10.flip;
    drw.A_r10.plot(rotor_construction);
    
    %Line P11 - P10
    drw.L_r11_10=Line();
    drw.L_r11_10.def(drw.A_r11.C2,drw.A_r10.C1);
    drw.L_r11_10.plot(rotor_construction);
    
    % Arc between points P10-P16, with origin at 0,0
    drw.A_r10_16 = Arc();
    drw.A_r10_16.def(drw.A_r10.C2,P_r16,[]);
    drw.A_r10_16.plot(rotor_construction);
    
    % Arc between points A_r10.C2-P15, with origin at 0,0
    drw.A_r10_15 = Arc();
    drw.A_r10_15.def(drw.A_r10.C2,P_r15,[]);
    drw.A_r10_15.plot(rotor_construction);
    
    %Line P17 - P12
    drw.L_r13_12=Line();
    drw.L_r13_12.def(P_r13,P_r12);
    drw.L_r13_12.plot(rotor_construction);
    
else
    % Arc between points P15-P16-P0, with origin at 0,0
    drw.A_r15_16 = Arc();
    drw.A_r15_16.def(P_r15,P_r16,[]);
    drw.A_r15_16.plot(rotor_construction);
    
end

%Line P17 - P15
drw.L_r17_15=Line();
drw.L_r17_15.def(P_r17,P_r15);
drw.L_r17_15.plot(rotor_construction);


%up to now drw structure has only one row, all elements will be
%mirrored in the following for loop, with mirrored values in second row



%% Mirror all previous primitives around symmetry axis
fn = fieldnames(drw(1));
for k=1:numel(fn)
    temp=copy(drw(1).(fn{k}));
    temp.mrr(pi/2);
    temp.plot(rotor_construction);
    drw(2).(fn{k})=temp; %mirrored primitives
end

%% Contruct rotor and shaft

%rotor and shaft are not mirrored so they will have only one row thus
%assigning values in drw(1), second row will be empty []

% Arc P18 - P17
drw(1).A_r18_17=Arc();
drw(1).A_r18_17.def(P_r18,P_r17,P_r0);
drw(1).A_r18_17.plot(rotor_construction);

% Arc P13 - P14
drw(1).A_r13_14=Arc();
drw(1).A_r13_14.def(P_r13,P_r14,P_r0);
drw(1).A_r13_14.plot(rotor_construction);


%close(gcf);
h(1)=subplot(2,2,[1 3]);





%% Rotate all primitives for -tau_pole/2 angle
fn = fieldnames(drw);
for k=1:numel(fn)
    for j=1:2
        if ~isempty(drw(j).(fn{k}))
            drw(j).(fn{k}).rot(-(pi/2-tau_pole/2));
            %drw(j).(fn{k}).plot(rotor_construction);            
            klasa=class(drw(j).(fn{k}));
            switch klasa
                case 'Arc'
                    for i=1:numel(drw(j).(fn{k}).Or.x)
                        plot(drw(j).(fn{k}).x(i,:),drw(j).(fn{k}).y(i,:),'b');
                        hold on
                        scatter(drw(j).(fn{k}).C1.x(i),drw(j).(fn{k}).C1.y(i),'r');
                        scatter(drw(j).(fn{k}).C2.x(i),drw(j).(fn{k}).C2.y(i),'r');
                        scatter(drw(j).(fn{k}).Or.x(i),drw(j).(fn{k}).Or.y(i),'r');
                    end
                case 'Line'
                    for i=1:numel(drw(j).(fn{k}).P1.x)
                        plot(drw(j).(fn{k}).x(i,:),drw(j).(fn{k}).y(i,:),'k');
                        hold on
                        scatter(drw(j).(fn{k}).P1.x(i),drw(j).(fn{k}).P1.y(i),'r');
                        scatter(drw(j).(fn{k}).P2.x(i),drw(j).(fn{k}).P2.y(i),'r');
                    end
            end
            
        end
    end
end

daspect([1 1 1]);
title(['\color{black}','   Point, line and arc primitives'],'FontSize',22);

%% Create Rotor polyshape class
% polyshape class is used for feasibility check and plotting in Matlab

h(2)=subplot(2,2,[2 4]);



for j=1:2        %for each row in drw class
    for i=1:lay
        
        %% Magnets
        
        
        X= [ drw(j).A_r03M.x(i,:) drw(j).A_r02M.x(i,:) drw(j).A_r07M.x(i,:)  drw(j).A_r06M.x(i,:) ];
        Y= [ drw(j).A_r03M.y(i,:) drw(j).A_r02M.y(i,:) drw(j).A_r07M.y(i,:)  drw(j).A_r06M.y(i,:) ];
        
        k=2*(j+i-1);
        
        if i==1 && j==1
            Rotor(i)=Shape();
        else
            Rotor(end+1)=Shape();
        end
        
        Rotor(end).des("Magnet");
        Rotor(end).ply(X,Y,[]');
        Rotor(end).lay(i,j);
        Rotor(end).ost(['L',num2str(i),'_1Magnet',num2str(j)]);
        Rotor(end).rgn(plot_regions,tau_pole,poleVangle(i));
        Rotor(end).plot(plot_shapes);
        
        %% Air pockets inner
        
        X= [drw(j).A_r02M.x(i,:) drw(j).A_r07M.x(i,:) fliplr(drw(j).A_rA.x(i,:))];
        Y= [drw(j).A_r02M.y(i,:) drw(j).A_r07M.y(i,:) fliplr(drw(j).A_rA.y(i,:))];
        
        Rotor(end+1)=Shape();
        
        Rotor(end).ply(X,Y,[]);
        Rotor(end).lay(i,j);
        Rotor(end).poly=subtract(Rotor(end).poly,Rotor(end-1).poly);

        % if .des("Air") set output string to .ost('RotorAir')
        % else set output string to .ost('Rotor Pocket')
        
%         Rotor(end).des("Air"); 
%         Rotor(end).ost('RotorAir');
        
        Rotor(end).des("Epoxy"); 
        Rotor(end).ost('Rotor Pocket');
        
        
        
        Rotor(end).rgn(plot_regions,[],[]);
        Rotor(end).plot(plot_shapes);
        
         %% Air pockets outer
        
        X= [drw(j).A_r06M.x(i,:) drw(j).A_r03M.x(i,:) fliplr(drw(j).A_rC.x(i,:))];
        Y= [drw(j).A_r06M.y(i,:) drw(j).A_r03M.y(i,:) fliplr(drw(j).A_rC.y(i,:))];
        
        Rotor(end+1)=Shape();
        
        Rotor(end).ply(X,Y,[]);
        Rotor(end).lay(i,j);
        Rotor(end).poly=subtract(Rotor(end).poly,Rotor(end-1).poly);

        % if .des("Air") set output string to .ost('RotorAir')
        % else set output string to .ost('Rotor Pocket')
        
%         Rotor(end).des("Air"); 
%         Rotor(end).ost('RotorAir');
        
        Rotor(end).des("Epoxy"); 
        Rotor(end).ost('Rotor Pocket');
        
        
        
        Rotor(end).rgn(plot_regions,[],[]);
        Rotor(end).plot(plot_shapes);
        
        
        
        
        
    end
end

%% Shaft polyshape

X=[drw(1).A_r18_17.x drw(1).A_r13_14.x];
Y=[drw(1).A_r18_17.y drw(1).A_r13_14.y];
Rotor(end+1)=Shape();
Rotor(end).des("Shaft");
Rotor(end).ost('Shaft');
Rotor(end).ply(X,Y,[]);
Rotor(end).rgn(plot_regions,[],[]);
Rotor(end).plot(plot_shapes);





if nd > 0 %if notch exists
    %% Notch 1
    inner_N1.x=[drw(1).L_r13_12.P2.x drw(1).A_r11.x  drw(1).A_r10.x];
    inner_N1.y=[drw(1).L_r13_12.P2.y drw(1).A_r11.y  drw(1).A_r10.y];
    
    X=[ inner_N1.x drw(1).A_r10_15.x ];
    Y=[ inner_N1.y drw(1).A_r10_15.y ];
    
    Rotor(end+1)=Shape();
    Rotor(end).des("Notch");
    Rotor(end).ost('RotorAir');
    Rotor(end).ply(X,Y,[]);
    Rotor(end).rgn(plot_regions,[],[]);
    Rotor(end).plot(plot_shapes);
    
    %% Notch 2
    inner_N2.x=[drw(2).L_r13_12.P2.x drw(2).A_r11.x  drw(2).A_r10.x];
    inner_N2.y=[drw(2).L_r13_12.P2.y drw(2).A_r11.y  drw(2).A_r10.y];
    
    X=[ inner_N2.x drw(2).A_r10_15.x ];
    Y=[ inner_N2.y drw(2).A_r10_15.y ];
    
    Rotor(end+1)=Shape();
    Rotor(end).des("Notch");
    Rotor(end).ost('RotorAir');
    Rotor(end).ply(X,Y,[]);
    Rotor(end).rgn(plot_regions,[],[]);
    Rotor(end).plot(plot_shapes);
    
    
    %% Rotor polyshape including all shapes and holes
    X=[fliplr(drw(1).A_r13_14.x)  inner_N1.x drw(1).A_r10_16.x fliplr(drw(2).A_r10_16.x) fliplr(inner_N2.x)];
    Y=[fliplr(drw(1).A_r13_14.y)  inner_N1.y drw(1).A_r10_16.y fliplr(drw(2).A_r10_16.y) fliplr(inner_N2.y)];
    
else
    X=[fliplr(drw(1).A_r13_14.x)  drw(1).A_r15_16.x   fliplr(drw(2).A_r15_16.x)];
    Y=[fliplr(drw(1).A_r13_14.y)  drw(1).A_r15_16.y   fliplr(drw(2).A_r15_16.y)];
end

Rotor(end+1)=Shape();
Rotor(end).des("Rotor");
Rotor(end).ost('Rotor');
Rotor(end).ply(X,Y,[]);

%add all holes to determine the region
polyvec=[Rotor(1:end-1).poly];
polyin=union(polyvec);
Rotor(end).poly=subtract(Rotor(end).poly,polyin);
Rotor(end).plot(plot_shapes);
Rotor(end).rgn(plot_regions,[],[]);


%calculate proper rotor laminate area
Rotor(end).shape_area=area(Rotor(end).poly);

%create rotor outer boundaries again, removeholes is problematic,
%this is better method
% Rotor(end).poly=polyshape(X,Y);

Rotor(end).plot(plot_shapes);

linkaxes(h);
ylim([-10 60]);
xlim([0 100]);
daspect([1 1 1]);
