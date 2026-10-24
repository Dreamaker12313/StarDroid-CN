/* Small reusable MPQ reader. The archive may be a Uint8Array or sparse segments. */
globalThis.MPQDecoder = {
  async create() {
    let archive = null, memory, lastError='';
    const imports = {
      env: {
        archive_size: () => archive.length,
        read_archive: (dst, offset, n) => {
          if (offset + n > archive.length || n > 64*1024*1024) throw Error('MPQ read out of bounds');
          new Uint8Array(memory.buffer, dst, n).set(archive.subarray(offset, offset+n));
        },
      },
      wasi_snapshot_preview1: {fd_close:()=>0, fd_seek:()=>8,
        fd_write: (fd, ptr, count, written) => {
          const view = new DataView(memory.buffer); let n = 0;
          for(let i=0;i<count;i++) {
            const p=view.getUint32(ptr+8*i,true),len=view.getUint32(ptr+8*i+4,true);n+=len;
            if(fd===2)lastError=(lastError+new TextDecoder().decode(new Uint8Array(memory.buffer,p,len))).slice(-800);
          }
          view.setUint32(written,n,true); return 0;
        },
      },
    };
    const response = await fetch('./media-decoder.wasm');
    if (!response.ok) throw Error('Music decoder is missing');
    const {instance} = await WebAssembly.instantiate(await response.arrayBuffer(), imports);
    const x = instance.exports; memory = x.memory; x._initialize();
    return {read(source, name) {
      if (archive !== source) { x.asset_reset(); archive = source; }
      const encoded = new TextEncoder().encode(name+'\0');
      if (encoded.length > 256) throw Error('MPQ filename is too long');
      new Uint8Array(memory.buffer,x.asset_name(),encoded.length).set(encoded);
      let ptr;try {ptr=x.asset_read();}catch(e){throw Error(lastError.trim() || e.message);}
      const size = x.asset_size();
      return ptr && size ? new Uint8Array(memory.buffer,ptr,size).slice() : null;
    }};
  },
};
