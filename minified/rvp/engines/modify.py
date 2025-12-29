from __future__ import annotations
_F='apksigner'
_E='keytool'
_D='modify_keystore'
_C='apktool'
_B=True
_A=False
import os,shutil,subprocess
from pathlib import Path
from typing import Any
from typing import cast
from..context import Context
from..utils import TIMEOUT_PATCH
from..utils import require_input_apk
from..utils import run_command
from..utils import validate_and_require_dependencies
def _run_apktool(ctx,args,success_path,action):
	B=action;A=ctx;A.log(f"modify: {B} with apktool");C=[_C,*args]
	try:run_command(C,A,timeout=TIMEOUT_PATCH);return success_path.exists()
	except(subprocess.SubprocessError,OSError)as D:A.log(f"modify: {B} failed: {D}");return _A
def _modify_icon(ctx,decompiled_dir,icon_path):
	H='convert';F=decompiled_dir;E='magick';C=icon_path;A=ctx
	if not C or not C.exists():A.log('modify: No icon specified or icon file not found');return _A
	if not shutil.which(E)and not shutil.which(H):A.log('modify: ImageMagick not found, skipping icon modification');return _A
	G=F/'res'
	if not G.exists():A.log('modify: res directory not found in decompiled APK');return _A
	D=[A for A in G.iterdir()if A.is_dir()and(A.name.startswith('mipmap-')or A.name.startswith('drawable-'))]
	if not D:A.log('modify: No icon directories found');return _A
	A.log(f"modify: Replacing icons in {len(D)} directories");I=E if shutil.which(E)else H
	for J in D:
		for B in J.glob('ic_launcher*'):
			try:
				K=subprocess.run([I,str(C),'-resize','512x512',str(B)],capture_output=_B,text=_B,check=_A)
				if K.returncode==0:A.log(f"  ✓ Updated {B.relative_to(F)}")
				else:A.log(f"  ✗ Failed to update {B.name}")
			except OSError as L:A.log(f"  ✗ Error updating {B.name}: {L}")
	return _B
def _replace_server_url(ctx,decompiled_dir,old_url,new_url):
	L='utf-8';G=new_url;E=decompiled_dir;C=old_url;A=ctx;M=E/'smali';N=E/'smali_classes2';H=[A for A in[M,N]if A.exists()]
	if not H:A.log('modify: No smali directories found');return _A
	A.log(f"modify: Replacing '{C}' with '{G}' in Smali files");F=0;B=[]
	for I in H:
		try:
			J=subprocess.run(['grep','-rl','--include=*.smali',C,str(I)],capture_output=_B,text=_B,check=_A)
			if J.returncode==0:B.extend(Path(A.strip())for A in J.stdout.splitlines()if A.strip())
		except(OSError,subprocess.SubprocessError):A.log('modify: grep not available, falling back to slower file-by-file search');B=list(I.rglob('*.smali'));break
	if not B:A.log('modify: No files contain the target URL');return _A
	A.log(f"modify: Found {len(B)} files to check")
	for D in B:
		try:
			K=D.read_text(encoding=L,errors='ignore')
			if C in K:O=K.replace(C,G);D.write_text(O,encoding=L);F+=1;A.log(f"  ✓ Modified {D.relative_to(E)}")
		except(OSError,UnicodeError)as P:A.log(f"  ✗ Error processing {D.name}: {P}")
	A.log(f"modify: Modified {F} Smali file(s)");return F>0
def _decompile_apk(ctx,input_apk,output_dir):A=output_dir;return _run_apktool(ctx,['d','-f','-o',str(A),str(input_apk)],A,'Decompiling APK')
def _recompile_apk(ctx,decompiled_dir,output_apk):A=output_apk;return _run_apktool(ctx,['b','-f','-o',str(A),str(decompiled_dir)],A,'Recompiling APK')
def _sign_apk(ctx,unsigned_apk,signed_apk):
	G=signed_apk;D='KEYSTORE_PASS';A=ctx;A.log('modify: Signing APK');E=cast(dict[str,Any],A.options.get(_D,{}));C=Path(str(E.get('path',A.work_dir/'keystore.jks')));H=str(E.get('alias','key0'));I=str(E.get('password','android'))
	if not C.exists():
		A.log(f"modify: Creating new keystore at {C}");J=[_E,'-genkey','-v','-keystore',str(C),'-alias',H,'-keyalg','RSA','-keysize','2048','-validity','10000','-storepass:env',D,'-keypass:env',D,'-dname','CN=APK Modifier, OU=Dev, O=APK, L=City, S=State, C=US']
		try:B=os.environ.copy();B[D]=I;run_command(J,A,env=B)
		except(subprocess.SubprocessError,OSError)as F:A.log(f"modify: Keystore creation failed: {F}");return _A
	K=[_F,'sign','--ks',str(C),'--ks-key-alias',H,'--ks-pass','pass:env:KEYSTORE_PASS','--out',str(G),str(unsigned_apk)]
	try:B=os.environ.copy();B[D]=I;run_command(K,A,timeout=TIMEOUT_PATCH,env=B);return G.exists()
	except(subprocess.SubprocessError,OSError)as F:A.log(f"modify: Signing failed: {F}");return _A
def run(ctx):
	I='modify';A=ctx;A.log('modify: starting APK modifier');D=require_input_apk(A);validate_and_require_dependencies(A,[_C,'java',_E,_F],I,'Install with: apt-get install -y apktool default-jdk apksigner | Or on Arch: pacman -S android-tools jdk-openjdk');E=A.work_dir/I;E.mkdir(parents=_B,exist_ok=_B);B=E/'decompiled';J=E/f"{D.stem}.unsigned.apk";C=A.output_dir/f"{D.stem}.modified.apk"
	if not _decompile_apk(A,D,B):raise RuntimeError('modify: Decompilation failed')
	F=A.options.get('modify_icon')
	if F:K=Path(cast(str,F));_modify_icon(A,B,K)
	G=A.options.get('modify_server_url_old');H=A.options.get('modify_server_url_new')
	if G and H:_replace_server_url(A,B,str(G),str(H))
	if not _recompile_apk(A,B,J):raise RuntimeError('modify: Recompilation failed')
	if not _sign_apk(A,J,C):raise RuntimeError('modify: Signing failed')
	A.set_current_apk(C);L=cast(dict[str,Any],A.options.get(_D,{}));M=str(L.get('path','auto-generated'));A.metadata[I]={'icon_modified':bool(F),'url_replaced':bool(G and H),'signed_apk':str(C),'keystore':M};A.log(f"modify: APK modification complete → {C}")