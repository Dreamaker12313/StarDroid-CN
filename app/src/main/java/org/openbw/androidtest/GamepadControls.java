package org.openbw.androidtest;

import android.content.SharedPreferences;
import android.view.InputDevice;
import android.view.KeyEvent;
import android.view.MotionEvent;
import org.json.JSONArray;
import org.json.JSONObject;

/** Controller preferences and device-independent stick/button normalization. */
final class GamepadControls {
  static final int NONE=0, CLICK=1, ORDER=2, CANCEL=3, ATTACK=4, STOP=5, HOLD=6,
      LARVAE=7, PREVIOUS_GROUP=8, NEXT_GROUP=9, RECALL_GROUP=10, ASSIGN_GROUP=11,
      MENU=12, ZOOM_IN=13, ZOOM_OUT=14, PRECISION=15;
  static final int[] BUTTONS={KeyEvent.KEYCODE_BUTTON_A,KeyEvent.KEYCODE_BUTTON_B,
      KeyEvent.KEYCODE_BUTTON_X,KeyEvent.KEYCODE_BUTTON_Y,KeyEvent.KEYCODE_BUTTON_L1,
      KeyEvent.KEYCODE_BUTTON_R1,KeyEvent.KEYCODE_BUTTON_L2,KeyEvent.KEYCODE_BUTTON_R2,
      KeyEvent.KEYCODE_BUTTON_SELECT,KeyEvent.KEYCODE_BUTTON_START,
      KeyEvent.KEYCODE_BUTTON_THUMBL,KeyEvent.KEYCODE_BUTTON_THUMBR};
  static final String[] BUTTON_LABELS={"A / Cross","B / Circle","X / Square","Y / Triangle",
      "Left shoulder","Right shoulder","Left trigger","Right trigger","Select / View","Start / Menu",
      "Left stick press","Right stick press"};
  static final String[] ACTION_LABELS={"None","Select / click","Move / interact","Cancel / back",
      "Attack","Stop","Hold position","Select larvae","Previous group","Next group",
      "Recall group","Assign group","Game menu","Zoom in","Zoom out","Precision pointer"};
  volatile boolean enabled=true;
  boolean swapSticks;
  float pointerSpeed=1, cameraSpeed=1, deadZone=.18f;
  final int[] bindings=new int[BUTTONS.length];
  GamepadControls(){reset();}
  void reset(){
    enabled=true;swapSticks=false;pointerSpeed=cameraSpeed=1;deadZone=.18f;
    int[] defaults={CLICK,ORDER,ATTACK,CANCEL,PRECISION,RECALL_GROUP,PREVIOUS_GROUP,NEXT_GROUP,CANCEL,MENU,ASSIGN_GROUP,STOP};
    System.arraycopy(defaults,0,bindings,0,bindings.length);
  }
  void load(SharedPreferences prefs){
    reset();
    try{
      JSONObject j=new JSONObject(prefs.getString("gamepad-controls","{}"));
      enabled=j.optBoolean("enabled",true);swapSticks=j.optBoolean("swapSticks",false);
      pointerSpeed=finite(j.optDouble("pointerSpeed",1),.25f,3,1);
      cameraSpeed=finite(j.optDouble("cameraSpeed",1),.25f,3,1);
      deadZone=finite(j.optDouble("deadZone",.18),.05f,.5f,.18f);
      JSONArray b=j.optJSONArray("bindings");
      if(b!=null)for(int i=0;i<bindings.length&&i<b.length();i++){
        int action=b.optInt(i,bindings[i]);if(action>=0&&action<ACTION_LABELS.length)bindings[i]=action;
      }
    }catch(Exception ignored){reset();}
  }
  void save(SharedPreferences prefs){
    try{
      JSONArray b=new JSONArray();for(int action:bindings)b.put(action);
      JSONObject j=new JSONObject().put("version",1).put("enabled",enabled).put("swapSticks",swapSticks)
          .put("pointerSpeed",pointerSpeed).put("cameraSpeed",cameraSpeed).put("deadZone",deadZone).put("bindings",b);
      prefs.edit().putString("gamepad-controls",j.toString()).apply();
    }catch(Exception e){throw new IllegalStateException(e);}
  }
  int action(int key){for(int i=0;i<BUTTONS.length;i++)if(BUTTONS[i]==key)return bindings[i];return NONE;}
  static boolean button(int key){for(int k:BUTTONS)if(k==key)return true;return false;}
  static boolean source(int source){return (source&InputDevice.SOURCE_GAMEPAD)==InputDevice.SOURCE_GAMEPAD
      ||(source&InputDevice.SOURCE_JOYSTICK)==InputDevice.SOURCE_JOYSTICK;}
  static float finite(double value,float min,float max,float fallback){return Double.isNaN(value)||Double.isInfinite(value)?fallback:(float)Math.max(min,Math.min(max,value));}
  /** Rescale outside the dead zone; cubic blend keeps small movements precise. */
  static float axis(float value,float dead){
    if(Float.isNaN(value)||Float.isInfinite(value))return 0;
    float v=Math.min(1,Math.abs(value));if(v<=dead)return 0;
    v=(v-dead)/(1-dead);return Math.copySign(v*(.4f+.6f*v*v),value);
  }
  float axis(MotionEvent event,int axis){
    float flat=deadZone;InputDevice device=event.getDevice();
    if(device!=null){InputDevice.MotionRange range=device.getMotionRange(axis,event.getSource());if(range!=null)flat=Math.max(flat,range.getFlat());}
    return axis(event.getAxisValue(axis),Math.min(.9f,flat));
  }
  static float limit(float value,float max){return Math.max(0,Math.min(Math.max(0,max-1),value));}
  static int nextGroup(int current,int step){return (current+step+10)%10;}
}
