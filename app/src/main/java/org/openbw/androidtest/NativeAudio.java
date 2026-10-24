package org.openbw.androidtest;

import android.media.AudioAttributes;
import android.media.AudioFocusRequest;
import android.media.AudioFormat;
import android.media.AudioManager;
import android.media.AudioTrack;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;

/** A single streaming mixer retains channel priorities and stereo panning. */
final class NativeAudio implements AutoCloseable {
  private volatile boolean running = true;
  private final Thread thread;
  private volatile AudioTrack track;
  private final AudioManager manager;
  private final AudioFocusRequest focusRequest;
  private final Runnable focusChanged;
  private volatile boolean foreground, focused;

  NativeAudio(Context context, Runnable focusChanged) {
    this.focusChanged = focusChanged;
    manager = (AudioManager) context.getSystemService(Context.AUDIO_SERVICE);
    AudioAttributes attributes = new AudioAttributes.Builder()
        .setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build();
    focusRequest = new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)
        .setAudioAttributes(attributes).setAcceptsDelayedFocusGain(true)
        .setWillPauseWhenDucked(true)
        .setOnAudioFocusChangeListener(this::focus, new Handler(Looper.getMainLooper())).build();
    thread =
        new Thread(
            () -> {
              android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_AUDIO);
              try {
                int rate = 48000,
                    min =
                        AudioTrack.getMinBufferSize(
                            rate, AudioFormat.CHANNEL_OUT_STEREO, AudioFormat.ENCODING_PCM_16BIT);
                track =
                    new AudioTrack.Builder()
                        .setAudioAttributes(attributes)
                        .setAudioFormat(
                            new AudioFormat.Builder()
                                .setSampleRate(rate)
                                .setChannelMask(AudioFormat.CHANNEL_OUT_STEREO)
                                .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                                .build())
                        .setTransferMode(AudioTrack.MODE_STREAM)
                        .setBufferSizeInBytes(Math.max(min, 8192))
                        .setPerformanceMode(AudioTrack.PERFORMANCE_MODE_LOW_LATENCY)
                        .build();
                short[] buffer = new short[2048];
                outputVolume();
                track.play();
                while (running) {
                  NativeBridge.mix(buffer, rate);
                  int at = 0;
                  while (running && at < buffer.length) {
                    int n = track.write(buffer, at, buffer.length - at, AudioTrack.WRITE_BLOCKING);
                    if (n < 0) throw new IllegalStateException("Audio output " + n);
                    if (n == 0) {Thread.sleep(2); continue;}
                    at += n;
                  }
                }
              } catch (Exception e) {
                android.util.Log.e("StarDroid", "Native audio output", e);
              } finally {
                AudioTrack t = track;
                track = null;
                if (t != null) {
                  try {
                    t.stop();
                  } catch (Exception ignored) {
                  }
                  t.release();
                }
              }
            },
            "StarDroid audio");
    thread.start();
  }

  boolean canPlay() { return running && foreground && focused; }

  void focus(int change) {
    focused = change == AudioManager.AUDIOFOCUS_GAIN && foreground;
    outputVolume();
    focusChanged.run();
  }

  private void outputVolume() {
    AudioTrack t = track;
    if (t != null) try {t.setVolume(canPlay() ? 1 : 0);} catch (IllegalStateException ignored) {}
  }

  void foreground(boolean value) {
    foreground = value;
    if (value && running) {
      focused = manager != null && manager.requestAudioFocus(focusRequest) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED;
    } else {
      focused = false;
      if (manager != null) manager.abandonAudioFocusRequest(focusRequest);
    }
    outputVolume();
    focusChanged.run();
  }

  public void close() {
    running = false;
    foreground(false);
    AudioTrack t = track;
    if (t != null)
      try {
        t.pause();
        t.flush();
      } catch (Exception ignored) {
      }
    try {
      thread.join(1200);
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
    }
  }
}
