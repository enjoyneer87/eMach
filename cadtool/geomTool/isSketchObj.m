function isSketch=isSketchObj(interfaceName)
isSketch=any(contains(fieldnames(interfaceName.invoke),'OpenSketch'));
end