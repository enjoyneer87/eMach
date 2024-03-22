function jmag=callJmag(jmagVersion)
if nargin<1
jmagVersion ='222'
end
jmag = actxserver(strcat('designer.Application.',jmagVersion));

end
