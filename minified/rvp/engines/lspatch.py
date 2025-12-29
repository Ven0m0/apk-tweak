from __future__ import annotations
_D='lspatch.jar'
_C='lspatch_jar'
_B='lspatch_modules'
_A='lspatch'
import shutil,subprocess
from pathlib import Path
from typing import Any
from typing import cast
from..context import Context
from..utils import TIMEOUT_PATCH
from..utils import build_tool_command
from..utils import find_latest_apk
from..utils import require_input_apk
from..utils import run_command
from..utils import validate_and_require_dependencies
def _build_lspatch_cmd(ctx,input_apk,output_dir):
	E=output_dir;A=ctx;F=['-l','2','-o',str(E)]
	if shutil.which(_A):F=['-v','-l','2','-f','-o',str(E)]
	B=build_tool_command(_A,A,_C,_D,F);G=A.options.get(_B,[])
	for C in G:
		if isinstance(C,Path)or'/'in str(C):D=Path(C)
		else:D=A.work_dir/f"patches/lspatch/{C}.apk"
		if D.exists():B.extend(['-m',str(D)])
		else:A.log(f"lspatch: Module not found: {D}")
	if A.options.get('lspatch_manager_mode',False):B.extend(['--manager','--injectdex'])
	B.append(str(input_apk));return B
def _run_lspatch_cli(ctx,input_apk,output_dir):
	B=output_dir;A=ctx;E=_build_lspatch_cmd(A,input_apk,B);A.log(f"lspatch: running CLI → {B}")
	try:
		C=run_command(E,A,timeout=TIMEOUT_PATCH,check=False)
		if C.returncode==0:
			D=find_latest_apk(B)
			if D:A.log('lspatch: CLI execution successful');return D
		A.log(f"lspatch: CLI failed (exit code: {C.returncode})");return
	except(OSError,subprocess.SubprocessError)as F:A.log(f"lspatch: CLI error: {F}");return
def run(ctx):
	O='modules';N='patched_apk';M='method';L='java';E=True;A=ctx;A.log('lspatch: starting patcher');B=require_input_apk(A);validate_and_require_dependencies(A,[_A,L],_A,'Install from: https://github.com/LSPosed/LSPatch');P=A.options.get('lspatch_use_cli',E)
	if P and shutil.which(_A):
		F=A.work_dir/'lspatch_output';F.mkdir(parents=E,exist_ok=E);G=_run_lspatch_cli(A,B,F)
		if G:C=A.output_dir/f"{B.stem}.lspatch.apk";shutil.copy2(G,C);A.set_current_apk(C);A.metadata[_A]={M:'cli',N:str(C),O:A.options.get(_B,[])};A.log(f"lspatch: patching complete → {C}");return
	A.log('lspatch: using JAR-based approach');Q=A.options.get('tools',{});R=cast(dict[str,Any],Q);D=Path(R.get(_C,_D))
	if not D.exists():A.log(f"LSPatch jar not found at {D}",level=40);raise FileNotFoundError(f"LSPatch jar missing: {D}")
	H=[L,'-jar',str(D),'-l','2','-o',str(A.output_dir),str(B)];I=A.options.get(_B,[])
	for S in I:H.extend(['-m',str(S)])
	A.log(f"lspatch: Running patch on {B.name}");run_command(H,A);J=A.output_dir/f"{B.stem}-lspatched.apk"
	if J.exists():A.set_current_apk(J)
	else:
		K=find_latest_apk(A.output_dir)
		if K:A.set_current_apk(K)
		else:raise FileNotFoundError('LSPatch completed but output APK not found')
	A.metadata[_A]={M:'jar',N:str(A.current_apk),O:I};A.log(f"lspatch: patching complete → {A.current_apk}")