function mkDesignerEquation(freq,app)


Study.GetDesignTable().AddEquation("freE")
Study.GetDesignTable().GetEquation("freE").SetType(0)
Study.GetDesignTable().GetEquation("freE").SetExpression()
Study.GetDesignTable().GetEquation("freE").SetDescription("")
Study.GetDesignTable().GetEquation("freE").SetModeling(False)
Study.GetDesignTable().GetEquation("freE").SetTrueValue("")
Study.GetDesignTable().GetEquation("freE").SetFalseValue("")
Study.GetDesignTable().GetEquation("freE").SetDisplayName("")
end