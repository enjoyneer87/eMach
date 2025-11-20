# Robust Feasibility Verification and Region Inner-Point Detection Algorithmsfor Geometric Shape Objects in E-machine Optimization


Mathematical optimization is a very popular term in modern design of electrical machines and devices in general.  When designing a machine, special attention must be paid to the definition of parameters, parameter bounds, constraint functions, model feasibility, and computationally intensive calculations such as finite element analysis (FEA). Geometrically infeasible or non-feasible candidates are those that cannot be manufactured as real machines because they contain overlapping magnets, air pockets that overlap magnets or other air pockets, and generally undesirable geometric relationships. Non-feasible candidates should not be evaluated to determine performance, in order to save time and to prevent them to falsely appear as optimal solutions since they will never be considered for production. Also, for each closed region, the FEA software requires a precisely determined interior point to assign the material (air, electrical steel, permanent magnet, copper). This can be a major challenge for randomly generated complex geometries, typically in optimizations of high performance machines. To avoid drawing and creating geometry or material regions that are not valid, this paper proposes a robust method to verify feasibility and determine interior points on geometric shape objects. The proposed method can be applied to any existing geometric machine parameterization and used as an add-on to any optimization workflow.

This code contains minimal working code example.

Minimum system requirements to run the code:
* MATLAB Version: 9.6.0.1150989 (R2019a) Update 4
* Operating System: Microsoft Windows 10 
* Java Version: Java 1.8.0_181-b13 with Oracle Corporation Java HotSpot(TM) 64-Bit Server VM mixed mode
* Required toolbox: Mapping, Symbolic

