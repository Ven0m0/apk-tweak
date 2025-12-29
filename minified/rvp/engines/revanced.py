from __future__ import annotations
_K='final_apk'
_J='patch_bundles_applied'
_I='revanced_exclude_patches'
_H='revanced_patches'
_G='revanced-cli.jar'
_F='revanced_cli'
_E='optimized'
_D=False
_C='revanced-cli'
_B='revanced'
_A=True
import shutil
from pathlib import Path
from typing import Any
from typing import cast
from..context import Context
from..optimizer import optimize_apk
from..utils import build_tool_command
from..utils import require_input_apk
from..utils import run_cli_tool
from..utils import run_command
from..utils import validate_and_require_dependencies
def _build_revanced_cli_cmd(ctx,input_apk,output_apk):
	H='password';B=ctx;A=build_tool_command(_C,B,_F,_G,['patch']);I=B.options.get(_H,[])
	for C in I:
		if isinstance(C,str):A.extend(['-p',f"patches/revanced/{C}.rvp"])
		elif isinstance(C,dict):
			J=cast(str,C['name']);A.extend(['-p',f"patches/revanced/{J}.rvp"])
			for(F,E)in C.get('options',{}).items():
				if E is _A:A.append(f"-O{F}")
				elif E:A.append(f"-O{F}={E}")
	K=B.options.get(_I,[])
	for L in K:A.extend(['-e',str(L)])
	if B.options.get('revanced_exclusive',_D):A.append('--exclusive')
	G=B.options.get('revanced_keystore')
	if G:D=cast(dict[str,Any],G);A.extend(['--keystore',str(D['path']),'--keystore-entry-alias',str(D['alias']),'--keystore-password',str(D[H]),'--keystore-entry-password',str(D.get('entry_password',D[H]))])
	A.extend(['-o',str(output_apk),str(input_apk)]);return A
def _run_revanced_cli(ctx,input_apk,output_apk):A=output_apk;B=_build_revanced_cli_cmd(ctx,input_apk,A);return run_cli_tool(B,ctx,_B,A)
def _create_stub_apk(ctx,input_apk,patch_bundles_count):C=input_apk;A=ctx;B=A.output_dir/f"{C.stem}.revanced.apk";shutil.copy2(C,B);A.set_current_apk(B);A.metadata[_B]={_J:patch_bundles_count,_E:_D,_K:str(B),'stub_mode':_A};A.log(f"revanced: stub mode - copied to {B}")
def run(ctx):
	Y='patches';X='method';W='revanced_minify';V='revanced_debloat';U='revanced: Starting optimization phase';T='revanced_optimize';S='java';A=ctx;A.log('revanced: starting patcher');B=require_input_apk(A)
	if not validate_and_require_dependencies(A,[_C,S],_B,'Install with: yay -S revanced-cli-bin jdk17-openjdk',fallback=_A):_create_stub_apk(A,B,0);return
	Z=A.options.get('revanced_use_cli',_A)
	if Z and shutil.which(_C):
		I=A.output_dir/f"{B.stem}.revanced.apk"
		if _run_revanced_cli(A,B,I):
			E=A.options.get(T,_D)
			if E:A.log(U);D=A.output_dir/f"{B.stem}.revanced-opt.apk";optimize_apk(input_apk=I,output_apk=D,ctx=A,debloat=A.options.get(V,_A),minify=A.options.get(W,_A));A.set_current_apk(D)
			else:A.set_current_apk(I)
			A.metadata[_B]={X:'cli','patched_apk':str(A.current_apk),Y:A.options.get(_H,[]),_E:E};return
	A.log('revanced: using JAR-based multi-patch pipeline');a=A.options.get('tools',{});J=cast(dict[str,Any],a);K=Path(J.get(_F,_G));Q=Path(J.get('revanced_integrations','integrations.apk'));b=A.options.get('revanced_patch_bundles',[]);C=cast(list[str],b)
	if not C:
		R=J.get(Y,'patches.jar')
		if R:C=[str(R)]
	if not C:A.log('revanced: No patch bundles specified, using stub mode');_create_stub_apk(A,B,0);return
	if not K.exists():A.log(f"revanced: CLI jar not found at {K}, using stub mode");_create_stub_apk(A,B,len(C));return
	G=B;L=A.work_dir/_B;L.mkdir(parents=_A,exist_ok=_A)
	for(M,c)in enumerate(C,1):
		H=Path(c)
		if not H.exists():A.log(f"revanced: Patch bundle not found: {H}, skipping");continue
		A.log(f"revanced: Applying patch bundle {M}/{len(C)}: {H.name}")
		if M==len(C):N=L/f"{B.stem}.patched.apk"
		else:N=L/f"{B.stem}.patch{M}.apk"
		F=[S,'-jar',str(K),'patch','--patch-bundle',str(H),'--out',str(N)]
		if Q.exists():F.extend(['--merge',str(Q)])
		d=A.options.get('revanced_include_patches',[]);e=A.options.get(_I,[])
		for O in d:F.extend(['--include',O])
		for O in e:F.extend(['--exclude',O])
		F.append(str(G));run_command(F,A);G=N
	E=A.options.get(T,_A)
	if E:A.log(U);D=A.output_dir/f"{B.stem}.revanced.apk";optimize_apk(input_apk=G,output_apk=D,ctx=A,debloat=A.options.get(V,_A),minify=A.options.get(W,_A));A.set_current_apk(D);A.log(f"revanced: Optimization complete - {D}")
	else:P=A.output_dir/f"{B.stem}.revanced.apk";G.rename(P);A.set_current_apk(P);A.log(f"revanced: Patching complete (no optimization) - {P}")
	A.metadata[_B]={X:'jar-multi-bundle',_J:len(C),_E:E,_K:str(A.current_apk)}