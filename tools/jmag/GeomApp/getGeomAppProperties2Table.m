function getGeomAppProperties2Table(CoilTemplatePropertiesTable,CoilTemplate)
    
    for PropertyIndex=1:height(CoilTemplatePropertiesTable)
    CoilTemplatePropertiesTable.Flag(PropertyIndex)=CoilTemplate.GetProperty(CoilTemplatePropertiesTable.Property(PropertyIndex));
    end
    
end