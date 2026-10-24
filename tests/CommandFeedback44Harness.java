package org.openbw.androidtest;

/** Host JVM checks for the same slot/cost helpers shipped in the APK. */
public final class CommandFeedback44Harness {
  static void check(boolean ok, String message) {if (!ok) throw new AssertionError(message);}
  public static void main(String[] args) {
    for (String label : new String[]{"Covert Ops", "Terran Covert Ops"})
      check(CommandSlots.override(116, label, 0) == 6, "Covert Ops must be bottom left");
    for (String label : new String[]{"Physics Lab", "Terran Physics Lab"})
      check(CommandSlots.override(116, label, 0) == 7, "Physics Lab must be bottom middle");
    check(CommandSlots.override(116, "Lift Off", 8) == 8, "Lift Off slot displaced");
    for (int type : new int[]{1,16,99,100,104}) {
      check(CommandSlots.override(type,"Cloak",0)==6, "Ghost cloak displaced");
      check(CommandSlots.override(type,"Lockdown",0)==7, "Ghost lockdown displaced");
    }
    String[] f={"m","Marine","1","0","50","0","1","","Infantry","0","0","-1","-1","0","2","1"};
    check(CommandHint.describe(f,"").contains("50 minerals · 1 supply"), "Cost line lost supply");
    f[14]="1";check(CommandHint.describe(f,"").contains("0.5 supply"),"Half supply lost");
    System.out.println("PASS Science Facility addon slots, Ghost slots and cost text");
  }
}
