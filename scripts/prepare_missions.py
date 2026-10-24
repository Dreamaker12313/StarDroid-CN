#!/usr/bin/env python3
"""Generate native, engine and web catalogs from the same reviewed metadata."""
import json
from pathlib import Path
r = Path(__file__).resolve().parents[1]
missions = json.loads((r/'missions.json').read_text())
assert len({m['id'] for m in missions}) == len(missions)
assert len({m['code'] for m in missions}) == len(missions)
(r/'web/missions.js').write_text('/* Generated from missions.json. */\nwindow.OpenBWMissions = '+json.dumps(missions,separators=(',',':'))+';\n')
rows = ',\n        '.join('{'+','.join([str(m['code']),json.dumps(m['id']),json.dumps(m['title']),json.dumps(m['prefix']),str(m['game']=='broodwar').lower()])+'}' for m in missions)
source = r'''package org.openbw.androidtest;
/** Generated from missions.json; archive paths are an allowlist. */
final class CampaignCatalog {
    static final Object[][] ALL = {%s};
    static Object[] get(int code) { for(Object[] m:ALL)if(((Integer)m[0])==code)return m;throw new IllegalArgumentException("Unknown mission"); }
    static Object[] get(String id) { for(Object[] m:ALL)if(m[1].equals(id))return m;throw new IllegalArgumentException("Unknown mission"); }
    static String id(int code) { return (String)get(code)[1]; }
    static boolean supported(String id) { for(Object[] m:ALL)if(m[1].equals(id))return true;return false; }
    static boolean supported(int code) { for(Object[] m:ALL)if(((Integer)m[0])==code)return true;return false; }
    static String title(int code) { return (String)get(code)[2]; }
    static String prefix(String id) { return ((String)get(id)[3]).replace('/', '\\'); }
    static String missionForPath(String path) { for(Object[] m:ALL)if(path.toLowerCase(java.util.Locale.ROOT).equals(((String)m[3]).replace('/', '\\')+"staredit\\scenario.chk"))return (String)m[1];throw new IllegalArgumentException("Unknown mission path"); }
    static boolean expansion(int code) { return (Boolean)get(code)[4]; }
}
''' % rows
(r/'app/src/main/java/org/openbw/androidtest/CampaignCatalog.java').write_text(source)
header = '// Generated from missions.json.\nstruct web_campaign_entry { int code, player, race; bool expansion; const char* prefix; };\nstatic const web_campaign_entry web_campaigns[] = {\n'
header += ',\n'.join('    {'+','.join([str(m['code']),str(m['player']),str(m['race']),str(m['game']=='broodwar').lower(),json.dumps(m['prefix'])])+'}' for m in missions)
header += '\n};\n'
(r/'web/campaign_catalog.h').write_text(header)
if (r/'build-engine/web').exists(): (r/'build-engine/web/campaign_catalog.h').write_text(header)
