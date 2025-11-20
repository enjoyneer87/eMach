function [A] = fillet_A2L(P1,P,P2,OR,r_fill,enable_plot)
%P1 first line point
%P line and arc intersection point
%P2 second point
%r_fill fillet radius
% OR is the origin point of the arc
%if OR is [], that means arc origin is 0,0


C1=Point();
C2=Point();
Or=Point();


if isempty(OR)
    OR=Point();
    OR.x=zeros(1,numel(P1.x));
    OR.y=zeros(1,numel(P1.x));
    OR.c2p;
end

R=sqrt((OR.x+P2.x).^2+(OR.y+P2.y).^2);


k=(P.y-P1.y)./(P.x-P1.x);
lay=numel(P2.y);


%% Izracunaj maksimalne radijuse

r_1=sqrt((P1.x-P.x).^2+(P1.y-P.y).^2);
r_2=sqrt((P2.x-P.x).^2+(P2.y-P.y).^2);

idx=r_1>r_2;
temp=r_1;
temp(idx)=r_2(idx);
r_fill=r_fill.*temp; % scale boundaries



%% Rubni uvjet 1
hack1=0.75;
R_max_1=hack1*r_1;
idx=find(r_fill > R_max_1);
if ~isempty(idx)
    r_fill(idx)=hack1*r_1(idx); %Hack ako je r_fill > d(P1-P)
    %disp(['Fillet radius is bigger than allowed, radius set to ',num2str(r_1)]);
end


%%  Rubni uvjet 2
hack2=0.5;
R_max_2=hack2*r_2;
idx=find(r_fill > R_max_2);
if ~isempty(idx)
    r_fill(idx)=hack2*r_2(idx); %Hack ako je r_fill > d(P2-P)
    %disp(['Fillet radius is bigger than allowed, radius set to ',num2str(r_1)]);
end


%% Minimum manufacturable fillet
r_minimum=0.3;

for i=1:lay
    if (r_fill(i) < r_minimum) && (R_max_1(i) > r_minimum) && (R_max_2(i) > r_minimum)
        r_fill(i)=r_minimum;
        %disp(['Fillet radius is too small, radius set to ',num2str(r_minimum)]);
    end
end

r=r_fill;

%%

% y=k(x-P1.x)+P1.y +/- r*sqrt(1+k.^2)
% line p is defined as ax + by + c = 0

% [A,B]=linecircleintersection(k, -k.*P1.x+P1.y+r.*sqrt(1+k.^2)  ,OR.x ,OR.y ,R);

a=k;
b=-1;
cp=P1.y-k.*P1.x;



c1= r.*sqrt(1+k.^2)+cp;
c2=-r.*sqrt(1+k.^2)+cp;

%distance P2 to line p, closer line is the correct
d_OR_p1=abs(a.*P2.x+b.*P2.y+c1)./sqrt(a.^2+b.^2);
d_OR_p2=abs(a.*P2.x+b.*P2.y+c2)./sqrt(a.^2+b.^2);

%find line closest to the arc centre to avoid double sollutions
c=c1;
idx=find(d_OR_p1>d_OR_p2);
if ~isempty(idx)
    c(idx) = c2(idx);
end


%get filet origin
syms x_Or y_Or

assume(y_Or >0);
assume(x_Or >0);
f1=  a.*x_Or+b.*y_Or+c==0;

if P1.R > P2.R %important to have fillet on proper side
    R_f2=R+r;
else
    R_f2=R-r;
end

f2= (x_Or-OR.x).^2+(y_Or-OR.y).^2==R_f2.^2;


%         x=linspace(1,30);
%         y=k(1)*(x-P1.x(1))+P1.y(1)+c;
%         plot(x,y)
%         plot(P1.x,P1.y,'*')


for i=1:lay
    S=vpasolve([f1(i),f2(i)],[x_Or, y_Or]);
    Or.x(i)=double(S.x_Or);
    Or.y(i)=double(S.y_Or);
end


beta1=atan2(Or.y-OR.y,Or.x-OR.x);
C1.x=OR.x+R.*cos(beta1);
C1.y=OR.y+R.*sin(beta1);



syms x_C2 y_C2
f1= y_C2-P1.y==k.*(x_C2-P1.x);
f2= y_C2-Or.y==-k.^-1.*(x_C2-Or.x);


for i=1:lay
    
    if k(i)==0
        C2.x(i)=Or.x(i);
        C2.y(i)=P1.y(i);
    else
        S=vpasolve([f1(i),f2(i)],[x_C2,y_C2]);
        C2.x(i)=double(S.x_C2);
        C2.y(i)=double(S.y_C2);
    end
end

A=Arc();

C1.c2p;
C2.c2p;
Or.c2p;


A.def(C1,C2,Or);

Or.plot(enable_plot);
C1.plot(enable_plot);
C2.plot(enable_plot);
A.plot(enable_plot);


end

