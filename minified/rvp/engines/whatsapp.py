from __future__ import annotations
import shutil,subprocess,sys
from pathlib import Path
from typing import cast
from..context import Context
from..utils import clone_repository
from..utils import require_input_apk
from..utils import validate_and_require_dependencies
WHATSAPP_PATCHER_REPO='https://github.com/Schwartzblat/WhatsAppPatcher'
WHATSAPP_FEATURES=['Signature Verifier Bypass','Enable all AB tests','Keep revoked for all messages','Disable read receipts','Save view once media']
def run(ctx):
	R='whatsapp_ab_tests';Q='main.py';P='whatsapp_temp_dir';O=False;N='whatsapp';B=True;A=ctx;A.log('whatsapp: starting WhatsApp APK patcher');I=require_input_apk(A)
	if not validate_and_require_dependencies(A,['java'],N,'Install with: pacman -S jdk-openjdk or apt-get install openjdk-17-jre',fallback=B):return
	J=A.options.get('whatsapp_patcher_path')
	if J:C=Path(cast(str,J))
	else:
		C=A.work_dir/'whatsapp-patcher'
		if not clone_repository(WHATSAPP_PATCHER_REPO,C,A):A.log('whatsapp: failed to obtain patcher');return
		K=C/'requirements.txt'
		if K.exists():A.log('whatsapp: installing Python dependencies');subprocess.run([sys.executable,'-m','pip','install','-q','-r',str(K)],check=O)
	E=A.output_dir/f"{I.stem}.whatsapp-patched.apk";L=A.options.get(P);G=Path(L)if L else A.work_dir/'whatsapp_temp';G.mkdir(parents=B,exist_ok=B);F=C/'whatsapp_patcher'/Q
	if not F.exists():F=C/Q
	if not F.exists():A.log(f"whatsapp: main.py not found in {C}");return
	M=[sys.executable,str(F),'-p',str(I),'-o',str(E),'--temp-path',str(G)]
	if A.options.get(R,B):M.append('--ab-tests')
	H=A.options.get('whatsapp_timeout',1200);A.log(f"whatsapp: running patcher (timeout: {H}s)");A.log(f"whatsapp: features: {', '.join(WHATSAPP_FEATURES)}")
	try:
		D=subprocess.run(M,capture_output=B,text=B,cwd=C,timeout=H,check=O)
		if D.returncode==0 and E.exists():A.set_current_apk(E);A.log(f"whatsapp: success → {E}");A.metadata[N]={'patched_apk':str(E),'features':WHATSAPP_FEATURES,'ab_tests_enabled':A.options.get(R,B)}
		else:
			A.log(f"whatsapp: patching failed (exit code: {D.returncode})")
			if D.stderr:A.log(f"whatsapp: stderr: {D.stderr[:500]}")
			if D.stdout:A.log(f"whatsapp: stdout: {D.stdout[:500]}")
	except subprocess.TimeoutExpired:A.log(f"whatsapp: patching timed out after {H} seconds")
	except(OSError,subprocess.CalledProcessError)as S:A.log(f"whatsapp: patching error: {S}")
	finally:
		if not A.options.get(P):shutil.rmtree(G,ignore_errors=B)