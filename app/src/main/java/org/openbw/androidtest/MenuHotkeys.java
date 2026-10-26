package org.openbw.androidtest;

import java.util.*;

/** Assign visible, unique menu shortcuts without changing the original captions. */
final class MenuHotkeys {
  static final class Entry {
    final String id, source, label;
    int key;
    String shown;
    Entry(String id,String label) {
      this.id=id;this.source=label==null?"":label;
      this.label=PortText.text(source);this.shown=this.label;
    }
  }

  private String context="";
  private final Map<String,Integer> previous=new HashMap<>();

  void assign(String nextContext,List<Entry> entries) {
    nextContext += "|"+PortText.language;
    if(!context.equals(nextContext)){previous.clear();context=nextContext;}
    Set<Integer> used=new HashSet<>();
    for(Entry e:entries)e.key=0;
    // Reserve all original keys first, even for a temporarily disabled button.
    for(Entry e:entries) {
      int key=MenuLabels.mnemonic(e.label);
      if(key!=0&&used.add(key))e.key=key;
    }
    // A changing value or enabled state must not reshuffle an existing button.
    for(Entry e:entries)if(e.key==0&&!NativeArt.clean(e.label).trim().isEmpty()){
      Integer key=previous.get(e.id);
      if(key!=null&&used.add(key))e.key=key;
    }
    for(Entry e:entries) {
      String plain=NativeArt.clean(e.label);
      if(e.key==0&&!plain.trim().isEmpty()) {
        String title=plain;int colon=title.indexOf(':');if(colon>=0)title=title.substring(0,colon);
        String candidates=initials(title)+letters(title)+title;
        // For captions written in another alphabet, prefer the English action
        // letter, then show that physical key explicitly in a compact suffix.
        candidates+=initials(NativeArt.clean(e.source))+NativeArt.clean(e.source)+"1234567890abcdefghijklmnopqrstuvwxyz";
        for(int i=0;i<candidates.length();i++){
          int key=ascii(candidates.charAt(i));
          if(key!=0&&used.add(key)){e.key=key;break;}
        }
      }
      e.shown=decorate(e.label,e.key);
      if(e.key!=0)previous.put(e.id,e.key);
    }
    if(previous.size()>256){previous.clear();for(Entry e:entries)if(e.key!=0)previous.put(e.id,e.key);}
  }

  private static String initials(String value) {
    StringBuilder out=new StringBuilder();boolean start=true;
    for(int i=0;i<value.length();i++){
      char ch=value.charAt(i);if(start&&ascii(ch)>='a')out.append(ch);
      start=Character.isWhitespace(ch)||ch=='/'||ch=='-';
    }
    return out.toString();
  }

  private static String letters(String value){
    StringBuilder out=new StringBuilder();for(int i=0;i<value.length();i++)if(ascii(value.charAt(i))>='a')out.append(value.charAt(i));return out.toString();
  }

  private static int ascii(char ch) {
    ch=Character.toLowerCase(ch);
    return ch>='a'&&ch<='z'||ch>='0'&&ch<='9'?ch:0;
  }

  static String decorate(String caption,int key) {
    if(key==0)return withoutMnemonic(caption);
    if(MenuLabels.mnemonic(caption)==key)return caption;
    String text=withoutMnemonic(caption);char reset=1;
    for(int i=0;i<text.length();i++){
      char ch=text.charAt(i);if(ch<32){if(ch!=9&&ch!=10&&ch!=18&&ch!=19)reset=ch;continue;}
      if(ascii(ch)==key)return text.substring(0,i)+'\u0004'+ch+reset+text.substring(i+1);
    }
    return text+"\u0001 [\u0004"+keyText(key)+"\u0001]";
  }

  private static String keyText(int key){return key==27?"Esc":String.valueOf(Character.toUpperCase((char)key));}

  private static String withoutMnemonic(String text){
    StringBuilder out=new StringBuilder();
    for(int i=0;i<text.length();i++){
      if(text.charAt(i)==4){
        int end=i+1;while(end<text.length()&&text.charAt(end)>=32)end++;
        String key=text.substring(i+1,end);
        if(end<text.length()&&(text.charAt(end)==1||text.charAt(end)==2)
            &&(key.length()==1||key.equalsIgnoreCase("Esc"))){out.append(key).append(text.charAt(end));i=end;continue;}
      }
      out.append(text.charAt(i));
    }
    return out.toString();
  }

  /** Keep the advertised key visible when a narrow button needs ellipsis. */
  static String fit(NativeArt.Font font,String caption,int width) {
    int key=MenuLabels.mnemonic(caption);
    String plain=NativeArt.clean(PortText.text(caption)).replace('\n',' ');
    if(font.measure(plain)<=width)return caption;
    String fitted=NativeResults.fit(font,plain,width);
    if(key==0)return fitted;
    for(int i=0;i<fitted.length();i++)if(ascii(fitted.charAt(i))==key)return decorate(fitted,key);
    String suffix=" [\u0004"+keyText(key)+"\u0001]";
    int room=width-font.measure(suffix);
    if(room>=font.measure("..."))return NativeResults.fit(font,plain,room)+suffix;
    return suffix.trim();
  }

  /** The game palette uses white for code 4, unlike the green glue menus. */
  static String paintCaption(NativeArt.Font font,String caption,int color){
    if(!font.game||color==3||color==5||MenuLabels.mnemonic(caption)==0)return caption;
    int at=caption.indexOf('\u0004');
    return caption.substring(0,at)+'\u0003'+caption.substring(at+1);
  }
}
