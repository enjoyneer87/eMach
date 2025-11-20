function [A] = fillet_L2L(P1,P,P2,r,enable_plot)
%P1 first point
%P intersecton point
%P2 second point
%r fillet radius value in per units 0 - 1

%define arc points
C1=Point();
C2=Point();
Or=Point();

m=numel(P1.x);
if numel(r) < m
    r_pu=linspace(r,r,m);
else
    r_pu=r;
end

angle = atan2((P.y - P1.y),(P.x - P1.x)) - atan2((P.y - P2.y),(P.x - P2.x));


PP1 = sqrt((P.x - P1.x).^2 + (P.y - P1.y).^2);
PP2 = sqrt((P.x - P2.x).^2 + (P.y - P2.y).^2);

max_R = min(PP1, PP2)/2; %(for polygon is better to divide this value by 2)
segment=r_pu.*max_R;

%% Minimum manufacturable fillet
r_minimum=0.3;

for i=1:m
    if (segment(i) < r_minimum) && (max_R(i) > r_minimum)
        segment(i)=r_minimum;
        %disp(['Fillet radius is too small, radius set to ',num2str(r_minimum)]);
    end
end


%segment = r./abs(tan(angle / 2))
%
%
%
%         for i=1:numel(max_R)
%             if segment(i) > max_R(i)
%                 segment(i) = max_R(i);
%                 R(i) = segment(i) * abs(tan(angle(i) / 2));
%                 disp(['Fillet radius is bigger than allowed, radius set to ',num2str(R(i))]);
%             else
%                 R(i) = r(i);
%             end
%         end

for i=1:m
    
    if segment(i)==0 %no fillet
        R=0;
        PC1=0;
        PC2=0;
        
        Or.x = P.x ;
        Or.y = P.y ;
        
        C1.x = P.x ;
        C1.y = P.y ;
        
        C2.x = P.x ;
        C2.y = P.y ;
    else
        
        R=segment.*abs(tan(angle / 2));
        PC1=segment;
        PC2=segment;
        
        PO = sqrt(R.^2 + segment.^2);
        
        C1.x = P.x -  ((P.x - P1.x).* PC1)./ PP1;
        C1.y = P.y -  ((P.y - P1.y).* PC1)./ PP1;
        
        C2.x = P.x -  ((P.x - P2.x).* PC2)./ PP2;
        C2.y = P.y -  ((P.y - P2.y).* PC2)./ PP2;
        
        C.x = C1.x + C2.x - P.x;
        C.y = C1.y + C2.y - P.y;
        
        
        dx = P.x  * 2 - C1.x  - C2.x ;
        dy = P.y  * 2 - C1.y  - C2.y ;
        
        
        PC = sqrt(dx.^2 + dy.^2);
        
        Or.x = P.x - (dx.* PO)./PC;
        Or.y = P.y - (dy.* PO)./PC;
    end
    
end





C1.c2p;
C2.c2p;
Or.c2p;


A=Arc();
A.def(C1,C2,Or);

C1.plot(enable_plot);
C2.plot(enable_plot);
Or.plot(enable_plot);
A.plot(enable_plot);



end

