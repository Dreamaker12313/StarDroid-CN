package org.openbw.androidtest;

import android.graphics.Bitmap;

/** JNI only. There is no JavaScript or WebView in the native application. */
final class NativeBridge {
  static {
    System.loadLibrary("openbw");
  }

  static native void open(int slot, String path);

  static native void close();

  static native void endGame();

  static native void init(int width, int height, int mission, int race);

  static native long[] multiplayerInit(int width,int height,int slot,int firstRace,int secondRace,boolean expansion);
  static native long[] configuredInit(int slot,int[] races,int[] controllers,int difficulty,boolean expansion,boolean ffa,boolean network,int[] teams,boolean teamGame,boolean heroMode);
  static native byte[] multiplayerSave();
  static native void multiplayerRestore(byte[] state);
  static native byte[] multiplayerCollect();
  static native long multiplayerHash();
  static native void multiplayerApply(byte[] first,byte[] second);
  static native void multiplayerApplyAll(byte[][] commands);
  static native void multiplayerStep();
  static native void multiplayerPeerLeft();

  static native void resize(int width, int height, double scale);

  static native void frame(Bitmap target, int steps, double milliseconds);

  private static native byte[] rawText(int query);
  static String text(int query) { return GameLanguage.decode(rawText(query)); }
  static native byte[] archiveText(String archivePath);
  static native byte[] mapScenario(String archivePath);

  static native int value(int query, int argument);

  static native void command(int op, int a, int b, int c, int d);

  static native byte[] asset(int archive, String name);

  static native byte[] chk();

  static native byte[] replay();
  static native byte[] replayInfo(byte[] data);
  static native byte[] replayScenario(byte[] data);
  static native void replayOpen(byte[] data);
  static native void replaySeek(int frame);
  static native void replayCancelSeek();

  static native byte[] saveState();

  static native void restoreState(byte[] snapshot);

  static native void seekSound(int channel, int milliseconds);

  static native int sound(byte[] wav, int channel, boolean loop);

  static native int campaignSound(int stringId);
  static native void campaignEffect(int stringId);

  static native void mix(short[] samples, int sampleRate);

  static native void audio(boolean paused, float effects, float music);

  static native boolean playing(int channel);
  static native double soundPosition(int channel);
  static native int scoreSound(byte[] fill,byte[] ending,int duration);

  /** Original imported cursor artwork, with its hotspot at the bitmap centre. */
  static native boolean cursor(Bitmap target);

  static native void wire(Bitmap target, int selectionIndex);

  static native void cargoWire(Bitmap target, int passengerIndex);

  static native int[] movieOpen(byte[] bytes, boolean audio);
  static native int[] movieOpenAsset(int slot, String path, boolean audio);

  static native void movieFrame(int id, double time, boolean loop, Bitmap target);

  static native void movieClose(int id);

  private NativeBridge() {}
}
