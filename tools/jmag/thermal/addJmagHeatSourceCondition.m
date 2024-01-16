function addJmagHeatSourceCondition(ModelObj,Steady2,ConditionName,setName)

Steady2.CreateCondition("HeatGeneration", ConditionName)
Steady2.GetCondition(ConditionName).SetValue("GenerationType", 1)
Steady2.GetCondition(ConditionName).ClearParts()
Steady2.GetCondition(ConditionName).AddSet(ModelObj.GetSetList().GetSet(setName), 0)

end