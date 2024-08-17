function [PeriodicAngle,periodicitySlots,OneSlotAngle]=calcMotorPeriodicity(Pole,Slot)
LCMMotor=lcm(Pole,Slot);
periodicitySlots = LCMMotor / Pole;
PeriodicAngle=360/LCMMotor*periodicitySlots;
OneSlotAngle=PeriodicAngle/periodicitySlots;
end