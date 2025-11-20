function [out] = Rnd(in,N)

%in range of random numbers
%N number of random vector elements

if numel(in)>1
    for i=1:N
        out(i)=(in(2)-in(1)).*rand(1,1) + in(1);
    end
else
    out=in;
end

end