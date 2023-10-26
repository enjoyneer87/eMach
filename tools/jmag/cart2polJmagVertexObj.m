function vertex=cart2polJmagVertexObj(startVertex)
x=startVertex.GetX;
y=startVertex.GetY;

[theta,Radius]=cart2pol(x,y);
vertex.theta=rad2deg(theta);
vertex.Radius=Radius;
vertex.x=x;
vertex.y=y;
end