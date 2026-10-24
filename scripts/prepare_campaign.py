#!/usr/bin/env python3
"""Add original and expansion campaign host to the generated Android web assets, after prepare_web.py."""
from pathlib import Path
import shutil, subprocess
r=Path(__file__).resolve().parents[1];d=r/'app/src/main/assets/game'
subprocess.run(['python3',str(r/'scripts/prepare_missions.py')],check=True)
s=(d/'openbw.js').read_text()
s=s.replace('out.push(await fetchMap(mapFile));', "out.push(mapFile === 'campaign' ? await OpenBWCampaign.load('./mission/', new URLSearchParams(location.search).get('campaign') || 'terran01') : await fetchMap(mapFile));")
s=s.replace('let audioCtx = null, masterGain = null;', 'let audioCtx = null, masterGain = null;\n  let missionUI = null;')
s=s.replace('const rec = { source, gain, playing: true };', 'const rec = { source, gain, playing: true, startedAt: audioCtx.currentTime };')
s=s.replace('const soundBuffers = [];', 'const failedSounds = new Set();\n  const soundBuffers = [];')
s=s.replace('    }, () => {});\n  };\n  const audio = {', '    }, () => { failedSounds.add(id); delete pendingPlay[id]; });\n  };\n  const audio = {')
s=s.replace("const wasmName = session.bot ? session.bot.module : 'openbw.wasm';", "const wasmName = session.campaign ? 'openbw-campaign.wasm' : session.bot ? session.bot.module : 'openbw.wasm';")
s=s.replace('if (slots.length > 1) {', 'if (session.campaign) {\n    x.openbw_init_campaign(...winSize(), session.campaign);\n  } else if (slots.length > 1) {',1)
anchor="  hb('boot:engine-ready');"
s=s.replace(anchor,anchor+'''
  if (session.campaign) {
    const voiceIds = new Map();let activeVoice = null;
    const stopVoice = () => {
      audio.js_sound_stop(100);
      for (const id of voiceIds.values()) delete pendingPlay[id];
      activeVoice = null;
    };
    missionUI = OpenBWCampaign.ui(x, memory, {
      play(index, ptr, len) {
        stopVoice(); ensureAudio();
        let id = voiceIds.get(index);
        if (id === undefined) { id = audio.js_sound_load(ptr, len); voiceIds.set(index, id); }
        activeVoice = id;
        audio.js_sound_play(id, 100, 112);
        return soundBuffers[id]?.duration * 1000 || 0;
      }, status() {
        const buffer = soundBuffers[activeVoice], channel = soundChannels[100];
        const ready = !!buffer && channel?.source.buffer === buffer;
        return {ready, failed: activeVoice === null || failedSounds.has(activeVoice),
          duration: buffer?.duration * 1000 || 0,
          position: ready ? Math.max(0, audioCtx.currentTime - channel.startedAt) * 1000 : 0};
      }, stop: stopVoice,
    });
    window.openbwCampaignStats = () => ({...missionUI.stats(), decodedVoices: [...voiceIds.values()].filter(id=>soundBuffers[id]).length, allocatedMissionBytes:assets[3].allocatedBytes});
    window.openbwAndroidSuspend = () => { missionUI.suspend(true); audioCtx?.suspend(); };
    window.openbwAndroidResume = () => { missionUI.suspend(false); audioCtx?.resume(); };
    $('overlay').style.display = 'none';
    await missionUI.briefing();
  }
''')
s=s.replace("if (!paused && (!over ||", "if (!paused && (!over ||")
s=s.replace('const stepped = advanced > 0;', 'const stepped = advanced > 0;\n      missionUI?.poll();')
s=s.replace("pauseBtn.classList.toggle('is-paused', paused);", "pauseBtn.classList.toggle('is-paused', paused);\n    if (session.campaign && audioCtx) { if (paused) audioCtx.suspend(); else audioCtx.resume(); }")
s=s.replace('if (audioCtx) audioCtx.resume().catch(() => {});', 'if (audioCtx && !paused) audioCtx.resume().catch(() => {});')
s=s.replace('androidSuspended = true; androidWasPaused = paused; paused = true;', 'androidSuspended = true; androidWasPaused = paused; paused = true;\n    missionUI?.suspend(true);')
s=s.replace('paused = androidWasPaused; androidSuspended = false;', 'paused = androidWasPaused; androidSuspended = false;\n    missionUI?.suspend(false);')
s+='''
// Native home screen launches this route only after the user's local bundle is ready.
const campaignMission = OpenBWMissions.find(m=>m.id===new URLSearchParams(location.search).get('campaign'));
if (campaignMission) {
  $('controls').style.display = 'none';
  boot({campaign:campaignMission.code, mission:campaignMission, slots:[{slot:campaignMission.player,race:campaignMission.race}], mySlot:campaignMission.player, mapFile:'campaign'}).catch(e=>{
    $('campaign-briefing').hidden=true; $('overlay').style.display='grid';
    setMsg('Mission failed to start: '+e.message); console.error(e);
  });
}
'''
(d/'openbw.js').write_text(s)
h=(d/'index.html').read_text();h=h.replace('</head>', '<link rel="stylesheet" href="campaign.css">\n<script src="missions.js"></script><script src="campaign.js"></script>\n</head>')
h=h.replace('<div id="resources">', (r/'web/campaign.html').read_text()+'\n<div id="resources">')
h=h.replace('<div id="topbar">','<div id="topbar">\n<button id="campaign-objectives-button" hidden>Objectives</button>')
(d/'index.html').write_text(h)
for f in ['campaign.js','campaign.css','missions.js']:shutil.copyfile(r/'web'/f,d/f)
print('Prepared original and Brood War campaign host.')
