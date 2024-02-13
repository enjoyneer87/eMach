function Obj=devgetGeomAppItemObj(Obj)
%% ItemObject 상속된거 추후 재귀상속-함수로 
    
methodList = methods(PartObj);
GetMethodList=methodList(contains(methodList,'Get'))

end