from __future__ import annotations
_D='string_cleaner'
_C='ignore'
_B='strings.xml'
_A='utf-8'
import re,zipfile
from pathlib import Path
from typing import NamedTuple
from..context import Context
from..utils import require_input_apk
class StringUsage(NamedTuple):name:str;is_used:bool;locations:list[str]
def _extract_string_names(xml_content):A=re.compile('<string\\s+name="([^"]+)"');return{A.group(1)for A in A.finditer(xml_content)}
def _find_string_references(content):B=content;A=set();C=re.compile('R\\.string\\.([a-zA-Z0-9_]+)');A.update(A.group(1)for A in C.finditer(B));D=re.compile('@string/([a-zA-Z0-9_]+)');A.update(A.group(1)for A in D.finditer(B));return A
def _analyze_apk_strings(apk_path,android_path,ctx):
	A=ctx;A.log('string_cleaner: analyzing APK for string usage');F=set();C=set();K={};M={'app_name','app_name_suffixed'}
	try:
		with zipfile.ZipFile(apk_path,'r')as D:
			N=[A for A in D.namelist()if A.endswith(_B)]
			for E in N:
				try:
					G=D.read(E).decode(_A,errors=_C);H=_extract_string_names(G);F.update(H)
					for B in H:K.setdefault(B,[]).append(E)
					A.log(f"string_cleaner: found {len(H)} strings in {E}")
				except(UnicodeDecodeError,Exception)as I:A.log(f"string_cleaner: error reading {E}: {I}")
			L=[A for A in D.namelist()if(A.endswith(('.xml','.kt','.java'))and'drawable'not in A)and not A.endswith(_B)];A.log(f"string_cleaner: scanning {len(L)} source files")
			for O in L:
				try:G=D.read(O).decode(_A,errors=_C);P=_find_string_references(G);C.update(P)
				except(UnicodeDecodeError,Exception):continue
	except(zipfile.BadZipFile,OSError)as I:A.log(f"string_cleaner: error analyzing APK: {I}");return{}
	C.update(M);J={}
	for B in F:Q=B in C;J[B]=StringUsage(name=B,is_used=Q,locations=K.get(B,[]))
	R=sum(1 for A in J.values()if not A.is_used);A.log(f"string_cleaner: analysis complete - {len(F)} total, {len(C)} used, {R} unused");return J
def _remove_unused_strings(apk_path,usage_map,ctx):
	D=apk_path;A=ctx;F={A for(A,B)in usage_map.items()if not B.is_used}
	if not F:A.log('string_cleaner: no unused strings to remove');return D
	A.log(f"string_cleaner: removing {len(F)} unused strings");E=A.work_dir/_D/f"{D.stem}.cleaned.apk";E.parent.mkdir(parents=True,exist_ok=True)
	try:
		with zipfile.ZipFile(D,'r')as I,zipfile.ZipFile(E,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as K:
			for B in I.namelist():
				G=I.read(B)
				if B.endswith(_B):
					try:
						C=G.decode(_A,errors=_C);L=len(C.splitlines())
						for M in F:N=re.compile(rf'^\s*<string\s+name="{re.escape(M)}"[^>]*>.*?</string>\s*$',re.MULTILINE);C=N.sub('',C)
						O=len(C.splitlines());J=L-O
						if J>0:A.log(f"string_cleaner: cleaned {B} (removed {J} lines)")
						G=C.encode(_A)
					except(UnicodeDecodeError,Exception)as H:A.log(f"string_cleaner: error processing {B}: {H}")
				K.writestr(B,G)
		A.log(f"string_cleaner: created cleaned APK: {E.name}");return E
	except(zipfile.BadZipFile,OSError)as H:A.log(f"string_cleaner: error creating cleaned APK: {H}");return D
def run(ctx):
	L='src/android/app/src/main';K=False;A=ctx;M=A.options.get('clean_unused_strings',K)
	if not M:A.log('string_cleaner: disabled, skipping');return
	H=A.options.get('android_source_path',L);N=H if isinstance(H,str)else L;C=require_input_apk(A);A.log(f"string_cleaner: analyzing {C.name}");D=_analyze_apk_strings(C,N,A)
	if not D:A.log('string_cleaner: no strings found or analysis failed');return
	B=[A for(A,B)in D.items()if not B.is_used];A.metadata[_D]={'total_strings':len(D),'unused_strings':len(B),'unused_names':sorted(B)}
	if B:
		A.log(f"string_cleaner: found {len(B)} unused strings:")
		for O in sorted(B)[:10]:A.log(f"  - {O}")
		if len(B)>10:A.log(f"  ... and {len(B)-10} more")
	I=A.options.get('remove_unused_strings',K)
	if I and B:
		E=_remove_unused_strings(C,D,A)
		if E!=C:F=C.stat().st_size;P=E.stat().st_size;G=F-P;J=G/F*100 if F>0 else 0;A.log(f"string_cleaner: size reduction: {G/1024:.2f} KB ({J:.2f}%)");A.metadata[_D]['size_reduction']={'bytes':G,'percentage':J};A.set_current_apk(E);A.log(f"string_cleaner: pipeline will continue with {E.name}")
	elif not I:A.log('string_cleaner: analysis only mode (set remove_unused_strings=true to remove)')