self.window=self;
importScripts('./mpq-decoder.js','./campaign.js','./ui-original.js','./menu-codec.js');
onmessage=async()=>{
 const names=[...['disk','xterr','xterron','xzerg','xzergon','xprot','xproton'].map(n=>'glue/expcampaign/'+n+'.smk'),'glue/title/title.pcx',...['palmm','palnl','palrt'].flatMap(p=>['backgnd.pcx','tfont.pcx','teffect.pcx','dlg.grp','tile.grp','pok.pcx','pcancel.pcx'].map(n=>'glue/'+p+'/'+n)),...['glumain','glulogin','glucmpgn','gluexpcmpgn','glugamemode','gluhist','glupok'].map(n=>'rez/'+n+'.bin'),...['etail','pintro','pcredit'].map(n=>'glue/mainmenu/'+n+'.pcx'),...['single','singleon','multi','multion','editor','editoron','exit','exiton'].map(n=>'glue/mainmenu/'+n+'.smk'),'glue/palmm/retail_ex.pcx','glue/login/plist.pcx',...['ptopl','ptopr','pbotl','pbotr','phist'].map(n=>'glue/campaign/'+n+'.pcx'),...['disk','terr','terron','zerg','zergon','prot','proton'].map(n=>'glue/campaign/'+n+'.smk')];
 try{
  const decoder=await MPQDecoder.create(),files={},fonts=await OpenBWOriginal.fonts();
  for(const archive of ['patch_rt.mpq','BROODAT.MPQ','STARDAT.MPQ']){
   const r=await fetch('./data/'+archive);if(!r.ok)continue;const bytes=new Uint8Array(await r.arrayBuffer());
   await OpenBWOriginal.recoverFonts([bytes],fonts);
   for(const name of names)if(!files[name]){const b=decoder.read(bytes,name);if(b)files[name]=b;}
   const soundDecoder=await MPQDecoder.create();
   for(const [name,b] of Object.entries(OpenBWOriginal.soundFiles(n=>soundDecoder.read(bytes,n))))if(!files['sound/glue/'+name+'.wav'])files['sound/glue/'+name+'.wav']=b;
  }
  // CD palette entries are optional, and isolated from both art and font decoders.
  try{const source=await OpenBWCampaign.load('./interface/','interface'),cd=await MPQDecoder.create();
   for(const n of ['backgnd.pcx','tfont.pcx','teffect.pcx','dlg.grp','tile.grp']){const name='glue/palcs/'+n,b=cd.read(source,name);if(b)files[name]=b;}
  }catch(e){console.info('Campaign palette import:',e.message);}
  const animationFiles={};for(const n of Object.keys(files))if(n.endsWith('.smk')){animationFiles[n]=files[n];delete files[n];}
  const clips=await decodeMenuClips(animationFiles);
  const sounds={};for(const n of OpenBWOriginal.soundNames){const key='sound/glue/'+n+'.wav';if(files[key]){sounds[n]=files[key];delete files[key];}}
  postMessage({files,fonts,clips,sounds},[...Object.values(files),...Object.values(fonts),...Object.values(clips).map(c=>c.rgba),...Object.values(sounds)].map(a=>a.buffer).filter((b,i,all)=>all.indexOf(b)===i));
 }catch(e){postMessage({error:e.message});}
};
