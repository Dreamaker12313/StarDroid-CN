package org.openbw.androidtest;

/** Process-wide ownership of imported-data mutations, independent of Activity lifetime. */
final class GameDataOperation {
  static final class Lease {
    final String kind;
    String message;
    private Lease(String kind) {this.kind=kind;message=kind;}
  }
  private static Lease current;
  private static String result="";
  static synchronized Lease begin(String kind) {
    if(current!=null)return null;
    current=new Lease(kind);return current;
  }
  static synchronized boolean busy(){return current!=null;}
  static synchronized boolean moving(){return current!=null&&current.kind.equals("Moving game data…");}
  static synchronized String message(){return current==null?result:current.message;}
  static synchronized void update(Lease lease,String message){if(lease!=null&&current==lease)current.message=message;}
  static synchronized void finish(Lease lease,String message){if(lease!=null&&current==lease){result=message;current=null;}}
}
