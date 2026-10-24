importScripts('./menu-codec.js');
onmessage=async({data})=>{try{const clips=await decodeMenuClips(data);postMessage({clips},Object.values(clips).map(c=>c.rgba.buffer));}catch(e){postMessage({error:e.message});}};
