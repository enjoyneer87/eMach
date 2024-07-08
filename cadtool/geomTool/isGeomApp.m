function isGA=isGeomApp(interfaceName)

isGA=any(contains(fieldnames(interfaceName.invoke),'SetVersion'));
end