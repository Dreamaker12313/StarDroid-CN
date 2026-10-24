window.OpenBWTesting = function(x, offline) {
  const $=id=>document.getElementById(id),root=$('testing-settings');
  root.hidden=!offline;
  let instant=false,used=false;
  const note=text=>{$('testing-status').textContent=text;};
  const usedCheat=()=>{used=true;$('go-replay').disabled=true;$('go-replay').textContent='Replay unavailable: cheats used';};
  $('test-money').onclick=()=>{if(!offline)return;x.openbw_test_money();usedCheat();note('Added 10,000 minerals and 10,000 gas to your player.');};
  $('test-instant').onchange=e=>{
    if(!offline)return;
    instant=e.target.checked;x.openbw_test_instant(instant?1:0);
    if(instant)usedCheat();
    note(instant?'Instant construction, training and research enabled for your player.':'Normal production times restored.');
  };
  $('test-reveal').onclick=()=>{if(!offline)return;x.openbw_reveal_map();usedCheat();note('Map revealed for this game.');};
  $('test-victory').onclick=()=>{
    if(!offline)return;usedCheat();x.openbw_debug_outcome(1);$('menu-resume').click();
  };
  $('test-reset').onclick=()=>{
    instant=false;$('test-instant').checked=false;x.openbw_test_instant(0);
    $('opt-speed').value='42';$('opt-speed').dispatchEvent(new Event('change'));
    note('Normal production and Fastest speed restored. Granted money and map reveal remain until a new game.');
  };
  window.openbwTestingStats=()=>({instant,used,offline,frameMs:+$('opt-speed').value,speed:42/+$('opt-speed').value});
};
