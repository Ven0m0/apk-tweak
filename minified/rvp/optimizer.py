from __future__ import annotations
_B=False
_A=True
import os,shutil
from concurrent.futures import ThreadPoolExecutor,as_completed
from fnmatch import fnmatch
from pathlib import Path
from.ad_patterns import AD_PATTERNS,AdPattern
from.constants import APKTOOL_PATH_KEY,DEFAULT_APKTOOL,DEFAULT_CPU_MULTIPLIER,DEFAULT_ZIPALIGN,MAX_WORKER_THREADS,ZIPALIGN_PATH_KEY
from.context import Context
from.utils import run_command
def decompile_apk(apk,output_dir,ctx):B=ctx;A=apk;C=output_dir/f"{A.stem}_decompiled";D=B.options.get(APKTOOL_PATH_KEY,DEFAULT_APKTOOL);E=[str(D),'d',str(A),'-o',str(C),'-f'];B.log(f"optimizer: Decompiling {A.name}");run_command(E,B);return C
def debloat_apk(decompiled_dir,ctx):
	E=decompiled_dir;B=ctx;B.log('optimizer: Starting debloat process');F=B.options.get('debloat_patterns',[])
	if not F:B.log('optimizer: No debloat patterns specified, skipping');return
	C=0;G=0;from fnmatch import fnmatch as I;H=set()
	for A in E.rglob('*'):
		if not A.exists()or A in H:continue
		D=str(A.relative_to(E));J=any(I(D,A)for A in F)
		if J:
			H.add(A)
			try:
				if A.is_file():K=A.stat().st_size;B.log(f"optimizer: Removing {D}");A.unlink();C+=1;G+=K
				elif A.is_dir():B.log(f"optimizer: Removing directory {D}");shutil.rmtree(A);C+=1
			except OSError as L:B.log(f"optimizer: Failed to remove {A.name}: {L}")
	B.log(f"optimizer: Debloat complete - removed {C} items ({G/1024/1024:.2f} MB from files)")
def minify_resources(decompiled_dir,ctx):
	C=decompiled_dir;B=ctx;B.log('optimizer: Starting resource minification');G=B.options.get('minify_patterns',['res/drawable-xxxhdpi/*','res/raw/*.mp3','res/raw/*.wav','assets/unused/*']);D=0;E=0
	for A in C.rglob('*'):
		if not A.is_file():continue
		if any(fnmatch(A.relative_to(C).as_posix(),B)for B in G):
			try:F=A.stat().st_size;H=A.relative_to(C);B.log(f"optimizer: Removing {H} ({F} bytes)");A.unlink();D+=1;E+=F
			except OSError as I:B.log(f"optimizer: Failed to remove {A.name}: {I}")
	B.log(f"optimizer: Minification complete - removed {D} files ({E} bytes)")
def _apply_patch_to_file(file_path,patterns,ctx):
	D='ignore';C='utf-8';B=file_path
	try:
		A=B.read_text(encoding=C,errors=D);E=A
		for(F,G,I)in patterns:A=F.sub(G,A)
		if A!=E:B.write_text(A,encoding=C,errors=D);return _A
		return _B
	except(OSError,UnicodeError)as H:ctx.log(f"optimizer: Error patching {B.name}: {H}");return _B
def patch_ads(decompiled_dir,ctx):
	A=ctx;A.log('optimizer: Starting regex-based ad patching');B=list(decompiled_dir.rglob('*.smali'))
	if not B:A.log('optimizer: No smali files found');return
	A.log(f"optimizer: Scanning {len(B)} smali files...");C=0;E=os.cpu_count()or 1;D=min(MAX_WORKER_THREADS,E+DEFAULT_CPU_MULTIPLIER);A.log(f"optimizer: Using {D} worker threads")
	with ThreadPoolExecutor(max_workers=D)as F:
		G={F.submit(_apply_patch_to_file,B,AD_PATTERNS,A):B for B in B}
		for H in as_completed(G):
			if H.result():C+=1
	A.log(f"optimizer: Ad patching complete - modified {C} files")
def recompile_apk(decompiled_dir,output_apk,ctx):B=output_apk;A=ctx;C=A.options.get(APKTOOL_PATH_KEY,DEFAULT_APKTOOL);D=[str(C),'b',str(decompiled_dir),'-o',str(B)];A.log(f"optimizer: Recompiling APK to {B.name}");run_command(D,A)
def zipalign_apk(input_apk,output_apk,ctx):B=input_apk;A=ctx;C=A.options.get(ZIPALIGN_PATH_KEY,DEFAULT_ZIPALIGN);D=[str(C),'-f','-v','4',str(B),str(output_apk)];A.log(f"optimizer: Running zipalign on {B.name}");run_command(D,A)
def optimize_apk(input_apk,output_apk,ctx,debloat=_A,minify=_A):
	E=output_apk;D=input_apk;A=ctx;A.log('optimizer: Starting optimization pipeline');C=A.work_dir/'optimizer';C.mkdir(parents=_A,exist_ok=_A);G=A.options.get('revanced_patch_ads',_B);B=decompile_apk(D,C,A)
	if debloat:debloat_apk(B,A)
	if minify:minify_resources(B,A)
	if G:patch_ads(B,A)
	F=C/f"{D.stem}_recompiled.apk";recompile_apk(B,F,A);zipalign_apk(F,E,A);A.log(f"optimizer: Optimization complete - {E}")