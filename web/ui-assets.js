/* Original interface art is decoded from the player's MPQs, never bundled. */
globalThis.OpenBWArt = (() => {
  function pcx(data, transparent=true, glassIndex=-1) {
    if (!data || data.length<897) throw Error('Missing interface image');
    const v=new DataView(data.buffer,data.byteOffset,data.byteLength);
    const width=v.getUint16(8,true)-v.getUint16(4,true)+1,height=v.getUint16(10,true)-v.getUint16(6,true)+1,stride=v.getUint16(66,true);
    if(data[0]!==10 || data[2]!==1 || data[3]!==8 || data[65]!==1 || width<1 || height<1 || width>2048 || height>2048 || stride<width || stride>4096) throw Error('Unsupported interface image');
    const indices=new Uint8Array(stride*height),palette=data.slice(-768);let p=128,o=0;
    while(o<indices.length) {
      if(p>=data.length-769)throw Error('Truncated interface image');
      let a=data[p++],n=(a&192)===192?a&63:1;
      if((a&192)===192){if(p>=data.length-769)throw Error('Truncated image run');a=data[p++];}
      if(!n || o+n>indices.length)throw Error('Invalid image run');indices.fill(a,o,o+n);o+=n;
    }
    const canvas=document.createElement('canvas');canvas.width=width;canvas.height=height;
    const ctx=canvas.getContext('2d'),im=ctx.createImageData(width,height);
    for(let y=0;y<height;y++)for(let x=0;x<width;x++) {
      const index=indices[y*stride+x],at=(y*width+x)*4;
      im.data.set(palette.subarray(index*3,index*3+3),at);im.data[at+3]=transparent&&index===0?0:index===glassIndex?153:255;
    }
    ctx.putImageData(im,0,0);return{canvas,palette,indices,stride};
  }
  function font(data, tint, palette=tint?.palette, options={}) {
    if(!data||String.fromCharCode(...data.subarray(0,4))!=='FONT')return null;
    const v=new DataView(data.buffer,data.byteOffset,data.byteLength),low=data[4],high=data[5],height=data[7],glyphs=new Map();
    if(high<low||!height||height>64||8+(high-low+1)*4>data.length)return null;
    // tfontgam has three 64-pixel rows. Glue fonts have their own one-row ramps.
    const game=(tint?.stride||0)>=64&&tint?.indices.length>=192;
    const colors=game?{2:[0,0],3:[0,1],4:[0,2],5:[0,3],6:[0,4],7:[0,5],8:[1,0],11:[0,6],14:[1,1],15:[1,2],16:[1,3],17:[1,4],20:[0,7],21:[1,5],22:[1,6],23:[1,7],24:[2,0],25:[2,1],26:[0,0],27:[2,2],28:[2,3],29:[2,4],30:[2,5],31:[2,7]}:{2:[0,0],3:[0,1],4:[0,2],5:[0,3],6:[0,4],13:[0,0],26:[0,0]};
    function glyph(code,color=2) {
      const key=code+':'+color;if(glyphs.has(key))return glyphs.get(key);
      if(code<low||code>high)return null;let p=v.getUint32(8+(code-low)*4,true);if(!p||p+4>data.length)return null;
      const w=data[p++],h=data[p++],ox=data[p++],oy=data[p++];if(w>64||h>64||ox+w>96||oy+h>height)return null;
      const c=document.createElement('canvas');c.width=Math.max(1,w+ox+1);c.height=height;c.advance=w+ox;
      const ctx=c.getContext('2d'),im=ctx.createImageData(c.width,c.height),ramp=colors[color]||colors[2];let n=0;
      while(n<w*h&&p<data.length){const b=data[p++];n+=b>>3;if(n>=w*h)break;const col=b&7;
        if(col){const at=((Math.floor(n/w)+oy)*c.width+n%w+ox)*4,index=tint?.indices[ramp[0]*tint.stride+ramp[1]*8+col];
          const rgb=index!==undefined?palette.subarray(index*3,index*3+3):[200,185,110];
          if(index!==0&&!(rgb[0]===255&&rgb[1]===0&&rgb[2]===255)){im.data.set(rgb,at);im.data[at+3]=255;}}
        n++;
      }
      ctx.putImageData(im,0,0);glyphs.set(key,c);return c;
    }
    // Glue screens/messages add a pixel; compact console status text does not.
    // Native 640x480 footage verifies both render paths (see REFERENCES.md).
    const advance=c=>c===32?Math.floor(data[6]/2):c===9?data[6]*2:glyph(c)?glyph(c).advance+(options.spacing??1):0;
    const measure=s=>[...s].reduce((n,c)=>n+(c.charCodeAt(0)<32&&c!=='\t'?0:advance(c.charCodeAt(0))),0);
    function draw(text,{width=0,align='left',color=2,lineHeight=options.lineHeight||height}={}) {
      const lines=[];let line='',x=0;
      for(const token of String(text).replaceAll('\r','').split(/(\n| +)/)){
        if(token==='\n'){lines.push(line);line='';x=0;continue;}
        const w=measure(token);if(width&&x&&x+w>width){lines.push(line.trimEnd());line='';x=0;if(/^ +$/.test(token))continue;}
        line+=token;x+=w;
      }
      lines.push(line.trimEnd());const c=document.createElement('canvas');c.width=Math.max(1,width||Math.max(...lines.map(measure)));c.height=Math.max(1,lines.length*lineHeight);
      const ctx=c.getContext('2d');let y=0,current=color,invisible=false;
      for(const line of lines){const controls=[...line].filter(c=>c==='\x12'||c==='\x13'),alignment=controls.length?(controls.at(-1)==='\x13'?'center':'right'):align;
        let x=alignment==='center'?Math.floor((c.width-measure(line))/2):alignment==='right'?c.width-measure(line):0;
        for(const letter of line){const code=letter.charCodeAt(0);if(code<32){if(code===1){current=color;invisible=false;}else if(code===9)x+=advance(code);else if(code===12)invisible=true;else if(colors[code]){current=code;invisible=false;}continue;}const g=glyph(code,current);if(g&&!invisible)ctx.drawImage(g,x,y);x+=advance(code);}y+=lineHeight;}
      return c;
    }
    draw.height=height;draw.measure=measure;return draw;
  }
  function label(button, draw, text=button.textContent) {
    if(!draw)return;const c=draw(text);c.className='sc-label';c.setAttribute('aria-hidden','true');
    button.setAttribute('aria-label',text);button.replaceChildren(c);
  }
  function rawFrame(data,id,palette) {
    if(!data || data.length<6)return null;
    const v=new DataView(data.buffer,data.byteOffset,data.byteLength);if(id<0 || id>=v.getUint16(0,true))return null;
    const at=6+id*8;if(at+8>data.length)return null;
    const w=data[at+2],h=data[at+3],p=v.getUint32(at+4,true);if(!w || !h || p+w*h>data.length)return null;
    const c=document.createElement('canvas');c.width=w;c.height=h;const ctx=c.getContext('2d'),im=ctx.createImageData(w,h);
    for(let i=0;i<w*h;i++){const index=data[p+i];im.data.set(palette.subarray(index*3,index*3+3),i*4);im.data[i*4+3]=index?255:0;}
    ctx.putImageData(im,0,0);return c;
  }
  function grpFrame(data,id,palette) {
    if(!data||data.length<6)return null;const v=new DataView(data.buffer,data.byteOffset,data.byteLength);
    if(id<0||id>=v.getUint16(0,true))return null;const at=6+id*8;if(at+8>data.length)return null;
    const w=data[at+2],h=data[at+3],base=v.getUint32(at+4,true);if(!w||!h||base+2*h>data.length)return null;
    const c=document.createElement('canvas');c.width=w;c.height=h;const ctx=c.getContext('2d'),im=ctx.createImageData(w,h);
    for(let y=0;y<h;y++){let p=base+v.getUint16(base+2*y,true),x=0;while(x<w){if(p>=data.length)throw Error('Truncated GRP');const b=data[p++],n=b&128?b&127:b&64?b&63:b;if(!n||x+n>w)throw Error('Invalid GRP run');if(b&128){x+=n;continue;}const repeat=b&64?data[p++]:-1;
      for(let i=0;i<n;i++,x++){if(p>data.length)throw Error('Truncated GRP');const index=repeat<0?data[p++]:repeat,o=(y*w+x)*4;im.data.set(palette.subarray(index*3,index*3+3),o);im.data[o+3]=255;}
    }}ctx.putImageData(im,0,0);return c;
  }
  function dialogFrame(data,palette,width,height) {
    const c=document.createElement('canvas');c.width=width;c.height=height;const ctx=c.getContext('2d'),tiles=Array.from({length:9},(_,i)=>grpFrame(data,i,palette));
    if(!tiles.every(Boolean))return null;
    for(let y=0;y<height;y+=8)for(let x=0;x<width;x+=8){const row=y===0?0:y>=height-8?2:1,col=x===0?0:x>=width-8?2:1;ctx.drawImage(tiles[row*3+col],x,y);}
    return c;
  }
  return{pcx,font,label,rawFrame,grpFrame,dialogFrame};
})();
