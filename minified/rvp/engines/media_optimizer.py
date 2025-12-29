from __future__ import annotations
_O='-codec:a'
_N='libvorbis'
_M='libmp3lame'
_L='--strip-all'
_K='--force'
_J='--quality'
_I='.ogg'
_H='.mp3'
_G='.png'
_F='ffmpeg'
_E='jpegoptim'
_D='optipng'
_C='pngquant'
_B=True
_A=False
import itertools,os,shutil,subprocess,zipfile
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path
from..context import Context
from..utils import check_dependencies
from..utils import require_input_apk
DPI_FOLDERS={'ldpi':120,'mdpi':160,'hdpi':240,'xhdpi':320,'xxhdpi':480,'xxxhdpi':640,'tvdpi':213,'nodpi':0}
def _get_tool_availability(ctx):
	B=[_C,_D,_E,_F];D,A=check_dependencies(B);C={B:B not in A for B in B}
	if A:ctx.log(f"media_optimizer: missing tools: {', '.join(A)}");ctx.log('media_optimizer: install via package manager (Arch: pacman -S pngquant optipng jpegoptim ffmpeg)')
	return C
def _optimize_png(ctx,png_path,quality='65-80'):
	A=png_path
	try:B=subprocess.run([_C,_J,quality,'--ext',_G,_K,str(A)],capture_output=_B,text=_B,timeout=30,check=_A);return B.returncode==0
	except(subprocess.TimeoutExpired,Exception)as C:ctx.log(f"media_optimizer: PNG optimization failed for {A.name}: {C}");return _A
def _optimize_png_worker(png_path,quality='65-80'):
	A=png_path
	try:B=subprocess.run([_C,_J,quality,'--ext',_G,_K,str(A)],capture_output=_B,text=_B,timeout=30,check=_A);return A,B.returncode==0
	except(subprocess.TimeoutExpired,Exception):return A,_A
def _optimize_png_optipng_worker(png_path,optimization_level=7):
	A=png_path
	try:B=subprocess.run([_D,f"-o{optimization_level}",str(A)],capture_output=_B,text=_B,timeout=60,check=_A);return A,B.returncode==0
	except(subprocess.TimeoutExpired,Exception):return A,_A
def _optimize_jpg(ctx,jpg_path,quality=85):
	A=jpg_path
	try:B=subprocess.run([_E,f"--max={quality}",_L,str(A)],capture_output=_B,text=_B,timeout=30,check=_A);return B.returncode==0
	except(subprocess.TimeoutExpired,Exception)as C:ctx.log(f"media_optimizer: JPEG optimization failed for {A.name}: {C}");return _A
def _optimize_jpg_worker(jpg_path,quality=85):
	A=jpg_path
	try:B=subprocess.run([_E,f"--max={quality}",_L,str(A)],capture_output=_B,text=_B,timeout=30,check=_A);return A,B.returncode==0
	except(subprocess.TimeoutExpired,Exception):return A,_A
def _optimize_audio(ctx,audio_path,output_path,bitrate='96k'):
	B=output_path;A=audio_path
	try:
		C=A.suffix.lower()
		if C==_H:D=_M
		elif C==_I:D=_N
		else:return _A
		E=subprocess.run([_F,'-i',str(A),_O,D,'-b:a',bitrate,'-y',str(B)],capture_output=_B,text=_B,timeout=60,check=_A)
		if E.returncode==0 and B.exists():shutil.move(B,A);return _B
		return _A
	except(subprocess.TimeoutExpired,Exception)as F:ctx.log(f"media_optimizer: Audio optimization failed for {A.name}: {F}");return _A
def _optimize_audio_worker(audio_path,bitrate='96k'):
	A=audio_path
	try:
		C=A.suffix.lower()
		if C==_H:D=_M
		elif C==_I:D=_N
		else:return A,_A
		B=A.with_suffix(A.suffix+'.tmp');E=subprocess.run([_F,'-i',str(A),_O,D,'-b:a',bitrate,'-y',str(B)],capture_output=_B,text=_B,timeout=60,check=_A)
		if E.returncode==0 and B.exists():shutil.move(B,A);return A,_B
		return A,_A
	except(subprocess.TimeoutExpired,Exception):return A,_A
def _extract_apk(ctx,apk,extract_dir):
	A=extract_dir
	try:
		with zipfile.ZipFile(apk,'r')as B:B.extractall(A)
		ctx.log(f"media_optimizer: extracted {apk.name} to {A}");return _B
	except(OSError,zipfile.BadZipFile)as C:ctx.log(f"media_optimizer: extraction failed: {C}");return _A
def _repackage_apk(ctx,extract_dir,output_apk):
	C=output_apk;B=extract_dir
	try:
		F={_G,'.jpg','.jpeg','.gif','.webp',_H,_I,'.mp4','.so','.ttf','.woff','.woff2'}
		with zipfile.ZipFile(C,'w')as D:
			for A in B.rglob('*'):
				if A.is_file():
					E=A.relative_to(B)
					if A.suffix.lower()in F:D.write(A,E,compress_type=zipfile.ZIP_STORED)
					else:D.write(A,E,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
		ctx.log(f"media_optimizer: repackaged to {C.name}");return _B
	except(OSError,zipfile.BadZipFile)as G:ctx.log(f"media_optimizer: repackaging failed: {G}");return _A
def _process_images(ctx,extract_dir,tools):
	W='media_optimizer: using pngquant for PNG optimization (lossy)';V='optipng_level';U='media_optimizer: using optipng for PNG optimization (lossless)';Q='jpg';K=tools;J=extract_dir;F='png';A=ctx;G={F:0,Q:0};E=list(J.rglob('*.png'));L=list(itertools.chain(J.rglob('*.jpg'),J.rglob('*.jpeg')));A.log(f"media_optimizer: found {len(E)} PNG, {len(L)} JPEG files");M=K.get(_C,_A);N=K.get(_D,_A);O=K.get(_E,_A);R=A.options.get('png_optimizer',_D)
	if not M and not N and not O:A.log('media_optimizer: no optimization tools available, skipping image optimization');return G
	X=os.cpu_count()or 1;S=min(X,8);A.log(f"media_optimizer: optimizing images with {S} shared workers")
	with ProcessPoolExecutor(max_workers=S)as H:
		D={}
		if E:
			if R==_D and N:
				A.log(U);I=A.options.get(V,7);P=I if isinstance(I,int)else 7
				for C in E:B=H.submit(_optimize_png_optipng_worker,C,P);D[B]=F,C
			elif R==_C and M:
				A.log(W)
				for C in E:B=H.submit(_optimize_png_worker,C);D[B]=F,C
			elif N:
				A.log(U);I=A.options.get(V,7);P=I if isinstance(I,int)else 7
				for C in E:B=H.submit(_optimize_png_optipng_worker,C,P);D[B]=F,C
			elif M:
				A.log(W)
				for C in E:B=H.submit(_optimize_png_worker,C);D[B]=F,C
			else:A.log('media_optimizer: no PNG optimization tools available')
		if O and L:
			for T in L:B=H.submit(_optimize_jpg_worker,T);D[B]=Q,T
		for B in as_completed(D):
			Y,Z=D[B];Z,a=B.result()
			if a:G[Y]+=1
	if not O:A.log('media_optimizer: jpegoptim not available, skipped JPEG optimization')
	A.log(f"media_optimizer: optimized {G[F]} PNG, {G[Q]} JPEG files");return G
def _process_audio(ctx,extract_dir,tools):
	D=extract_dir;A=ctx
	if not tools.get(_F,_A):A.log('media_optimizer: ffmpeg not available, skipping audio optimization');return 0
	B=list(itertools.chain(D.rglob('*.mp3'),D.rglob('*.ogg')));A.log(f"media_optimizer: found {len(B)} audio files")
	if not B:return 0
	F=os.cpu_count()or 1;E=min(F,8);A.log(f"media_optimizer: optimizing audio with {E} workers");C=0
	with ProcessPoolExecutor(max_workers=E)as G:
		H={G.submit(_optimize_audio_worker,A):A for A in B}
		for I in as_completed(H):
			K,J=I.result()
			if J:C+=1
	A.log(f"media_optimizer: optimized {C} audio files");return C
def _filter_dpi_resources(ctx,extract_dir,target_dpis):
	A=ctx;F=extract_dir/'res'
	if not F.exists():A.log('media_optimizer: no res/ directory found');return 0
	B={A.lower().strip()for A in target_dpis};B.add('nodpi');A.log(f"media_optimizer: keeping DPIs: {', '.join(sorted(B))}");C=0;D=[]
	for G in F.glob('drawable-*'):
		H=G.name;I=H.split('-')
		if len(I)<2:continue
		E=None
		for J in I[1:]:
			if J in DPI_FOLDERS:E=J;break
		if E and E not in B:shutil.rmtree(G);D.append(H);C+=1
	if D:A.log(f"media_optimizer: removed {C} DPI folders: {', '.join(D)}")
	else:A.log('media_optimizer: no DPI folders removed')
	return C
def run(ctx):
	B='media_optimizer';A=ctx;F=A.options.get('optimize_images',_A);G=A.options.get('optimize_audio',_A);C=A.options.get('target_dpi')
	if not(F or G or C):A.log('media_optimizer: no operations requested; skipping.');return
	H=require_input_apk(A);A.log(f"media_optimizer: starting (images={F}, audio={G}, dpi={C})");K=_get_tool_availability(A);L=A.work_dir/B;L.mkdir(parents=_B,exist_ok=_B);D=L/'extracted'
	if not _extract_apk(A,H,D):A.log('media_optimizer: extraction failed, aborting');return
	if B not in A.metadata:A.metadata[B]={}
	if F:O=_process_images(A,D,K);A.metadata[B]['images']=O
	if G:P=_process_audio(A,D,K);A.metadata[B]['audio']=P
	if C:
		if isinstance(C,str):M=[A.strip()for A in C.split(',')]
		else:M=C
		Q=_filter_dpi_resources(A,D,M);A.metadata[B]['dpi_folders_removed']=Q
	E=A.output_dir/f"{H.stem}.optimized.apk"
	if _repackage_apk(A,D,E):A.set_current_apk(E);A.log(f"media_optimizer: pipeline will continue with {E}");I=H.stat().st_size;R=E.stat().st_size;J=I-R;N=J/I*100 if I>0 else 0;A.log(f"media_optimizer: size reduction: {J/1024/1024:.2f} MB ({N:.1f}%)");A.metadata[B]['size_reduction']={'bytes':J,'percentage':N}
	else:A.log('media_optimizer: repackaging failed, pipeline will continue with original APK')