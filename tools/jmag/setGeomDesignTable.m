function setGeomDesignTable(setString,value,geomApp)
geomDocu=geomApp.GetDocument;
geomDesignTable=geomDocu.GetDesignTable;
geomDesignTable.EditStart()
geomDesignTable.AddEquation(setString)
geomDesignTable.GetEquation(setString).SetType(0)
geomDesignTable.GetEquation(setString).SetExpression(num2str(value))
geomDesignTable.GetEquation(setString).SetDescription("")
geomDesignTable.GetEquation(setString).SetRegistrationSource("")
geomDesignTable.GetEquation(setString).SetRegisterToDesigner(1)
geomDesignTable.GetEquation(setString).SetIsFactorKey(0)
geomDesignTable.GetEquation(setString).SetTrueValue("")
geomDesignTable.GetEquation(setString).SetFalseValue("")
geomDesignTable.GetEquation(setString).SetDisplayName("")
geomDesignTable.EditEnd()
end