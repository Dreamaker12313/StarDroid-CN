// MPQ decompression runs off the simulation thread and is discarded after a track.
self.window = self;
importScripts('./campaign.js', './mpq-decoder.js');
self.onmessage = async ({data}) => {
  try {
    const archive = await OpenBWCampaign.load(data.base==='./music-broodwar/'?data.base:'./music/', 'music', data.name);
    const decoder = await MPQDecoder.create();
    const bytes = decoder.read(archive, data.name);
    if (!bytes || bytes.length < 44 || String.fromCharCode(...bytes.subarray(0,4)) !== 'RIFF') throw Error('Invalid WAV track');
    self.postMessage({bytes, allocatedBytes:archive.allocatedBytes}, [bytes.buffer]);
  } catch(e) { self.postMessage({error:e.message}); }
};
