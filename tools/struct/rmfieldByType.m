function struct=rmfieldByType(struct,DataType)
   fieldNames=fieldnames(struct);
   for fieldIndex=1:length(fieldNames)
       fieldName=fieldNames{fieldIndex};
       if strcmp(class(struct.(fieldName)),DataType) 
           struct=rmfield(struct,fieldName);
       end
   end
end
