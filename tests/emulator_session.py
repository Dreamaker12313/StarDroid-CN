#!/usr/bin/env python3
"""Run a headless AVD and queued adb requests in one host network namespace.

Requires Google's SDK emulator, platform-tools and API 28 default x86_64 image
under .tools/sdk. Requests are JSON files in build-native/emulator/requests:
{"argv": ["install", "absolute/path.apk"]}. Results use the same basename.
Create build-native/emulator/stop to shut down. No game data is downloaded.
"""
import json, os, pathlib, subprocess, time
root = pathlib.Path(__file__).resolve().parents[1]
sdk = root / '.tools/sdk'
run = root / 'build-native/emulator'
avds = run / 'avd'
avd_name = os.environ.get('OPENBW_AVD_NAME') or 'feedback-' + str(time.time_ns())
avd = avds / (avd_name + '.avd')
avd.mkdir(parents=True, exist_ok=True)
requests = run / 'requests'; requests.mkdir(exist_ok=True)
results = run / 'results'; results.mkdir(exist_ok=True)
(run / 'stop').unlink(missing_ok=True)
(run / 'ready.json').unlink(missing_ok=True)
(avds / (avd_name + '.ini')).write_text(f'avd.ini.encoding=UTF-8\npath={avd}\ntarget=android-28\n')
(avd / 'config.ini').write_text('\n'.join([
    'AvdId=' + avd_name, 'avd.ini.encoding=UTF-8', 'hw.cpu.arch=x86_64',
    'hw.cpu.ncore=1', 'hw.ramSize=2048', 'hw.lcd.width=960', 'hw.lcd.height=540',
    'hw.lcd.density=160', 'hw.mainKeys=no', 'hw.keyboard=yes', 'hw.gpu.enabled=yes',
    'hw.gpu.mode=swiftshader_indirect', 'disk.dataPartition.size=2048M',
    f'image.sysdir.1={sdk}/system-images/android-28/default/x86_64/',
    'tag.id=default', 'abi.type=x86_64', 'showDeviceFrame=no', 'skin.dynamic=yes',
]) + '\n')
env = dict(os.environ, ANDROID_SDK_ROOT=str(sdk), ANDROID_AVD_HOME=str(avds),
           ANDROID_I_WANT_MY_TCG='yes')
adb = [str(sdk/'platform-tools/adb'), '-s', 'emulator-5554']
with (run/'emulator.log').open('w') as log:
    emulator = subprocess.Popen([str(sdk/'emulator/emulator'), '-avd', avd_name,
        '-partition-size', '2048', '-no-window', '-no-audio', '-no-snapshot', '-no-boot-anim', '-no-metrics', '-accel', 'off',
        '-gpu', 'swiftshader_indirect', '-feature', '-Vulkan,-EncryptUserData', '-ports', '5554,5555'],
        env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        for i in range(240):
            if (run/'stop').exists(): raise RuntimeError('Stopped')
            if emulator.poll() is not None: raise RuntimeError('Emulator exited; see emulator.log')
            try:
                p = subprocess.run(adb+['shell','getprop','sys.boot_completed'],env=env,
                    capture_output=True,text=True,timeout=10)
            except subprocess.TimeoutExpired:
                continue
            if i % 15 == 0:
                print('BOOT', i, repr(p.stdout.strip()), repr(p.stderr[-500:]), flush=True)
                try:
                    diag=subprocess.run(adb+['logcat','-d','-t','1000'],env=env,capture_output=True,text=True,timeout=10)
                    (run/'boot-logcat.txt').write_text(diag.stdout+diag.stderr)
                except subprocess.TimeoutExpired: pass
            if p.stdout.strip() == '1': break
            time.sleep(2)
        else: raise RuntimeError('Android did not finish booting')
        (run/'ready.json').write_text(json.dumps({'booted':True,'api':28,'acceleration':False}))
        print('ANDROID_BOOTED',flush=True)
        until=time.monotonic()+7200
        while time.monotonic()<until and not (run/'stop').exists():
            for request in sorted(requests.glob('*.json')):
                destination=results/request.name
                if destination.exists(): continue
                try:
                    args=json.loads(request.read_text())
                    p=subprocess.run(adb+args['argv'],env=env,capture_output=True,
                        text=True,timeout=args.get('timeout',180))
                    result={'exitCode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
                except Exception as e: result={'exitCode':-1,'error':str(e)}
                destination.write_text(json.dumps(result,indent=2))
                print(request.name,result['exitCode'],flush=True)
            time.sleep(.25)
    finally:
        try:
            subprocess.run(adb+['emu','kill'],env=env,capture_output=True,timeout=5)
        except (subprocess.TimeoutExpired, OSError): pass
        emulator.terminate()
        try: emulator.wait(timeout=5)
        except subprocess.TimeoutExpired:
            emulator.kill(); emulator.wait()
