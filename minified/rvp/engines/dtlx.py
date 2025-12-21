from __future__ import annotations
_B=True
_A=False
import shutil,subprocess,sys
from pathlib import Path
from..context import Context
from..utils import require_input_apk
DTLX_REPO_URL='https://github.com/Gameye98/DTL-X'
DTLX_NOT_FOUND_MSG=f"dtlx: DTL-X not found. Install from {DTLX_REPO_URL}"
def _write_report(report_file,apk_name,status,details):A=f"DTL-X Analysis Report for {apk_name}\n{'='*60}\n\nStatus: {status}\n{details}";report_file.write_text(A,encoding='utf-8')
def _check_dtlx():
	C='dtlx.py';D=[Path.home()/'DTL-X'/C,Path('/opt/DTL-X/dtlx.py'),Path('/usr/local/bin/dtlx.py')];A=next((A for A in D if A.is_file()),None)
	if A:return A
	B=shutil.which(C);return Path(B)if B else None
def _run_dtlx_analyze(ctx,apk,report_file):
	D=report_file;C=ctx;A=apk;E=_check_dtlx()
	if not E:C.log(DTLX_NOT_FOUND_MSG);_write_report(D,A.name,'FAILED',f"Reason: DTL-X not installed\n\nInstall DTL-X from: {DTLX_REPO_URL}\n");return _A
	C.log(f"dtlx: analyzing {A.name}...")
	try:
		B=subprocess.run([sys.executable,str(E),str(A)],capture_output=_B,text=_B,timeout=300,check=_A);F=[f"DTL-X Analysis Report for {A.name}",'='*60,'',f"Status: {'SUCCESS'if B.returncode==0 else'COMPLETED WITH WARNINGS'}",f"Exit Code: {B.returncode}",'','STDOUT:','-'*60,B.stdout if B.stdout else'(no output)','']
		if B.stderr:F.extend(['STDERR:','-'*60,B.stderr,''])
		D.write_text('\n'.join(F),encoding='utf-8');C.log(f"dtlx: analysis report saved to {D}");return _B
	except subprocess.TimeoutExpired:C.log('dtlx: analysis timed out after 5 minutes');_write_report(D,A.name,'TIMEOUT','Reason: Analysis exceeded 5 minute timeout\n');return _A
	except(OSError,subprocess.CalledProcessError)as G:C.log(f"dtlx: analysis failed: {G}");_write_report(D,A.name,'ERROR',f"Error: {G}\n");return _A
def _run_dtlx_optimize(ctx,apk,output_apk):
	F=output_apk;E=apk;A=ctx;G=_check_dtlx()
	if not G:A.log(DTLX_NOT_FOUND_MSG);return _A
	H=['--rmads4','--rmtrackers','--rmnop','--cleanrun'];A.log(f"dtlx: optimizing {E.name} with flags: {' '.join(H)}")
	try:
		B=A.work_dir/'dtlx_work';B.mkdir(parents=_B,exist_ok=_B);I=B/E.name;shutil.copy2(E,I);J=[sys.executable,str(G)]+H+[str(I)];C=subprocess.run(J,capture_output=_B,text=_B,cwd=B,timeout=600,check=_A);D=list(B.glob('*_patched.apk'))
		if not D:D=list(B.glob('*-patched.apk'))
		if D and C.returncode==0:shutil.copy2(D[0],F);A.log(f"dtlx: optimized APK saved to {F}");return _B
		A.log(f"dtlx: optimization failed (exit code: {C.returncode})")
		if C.stderr:A.log(f"dtlx: error: {C.stderr[:200]}")
		return _A
	except subprocess.TimeoutExpired:A.log('dtlx: optimization timed out after 10 minutes');return _A
	except(OSError,subprocess.CalledProcessError)as K:A.log(f"dtlx: optimization failed: {K}");return _A
def run(ctx):
	D='dtlx';A=ctx;E=A.options.get('dtlx_analyze',_A);F=A.options.get('dtlx_optimize',_A)
	if not(E or F):A.log('dtlx: neither analyze nor optimize requested; skipping.');return
	B=require_input_apk(A);A.log(f"dtlx: starting (analyze={E}, optimize={F}) on {B}.")
	if D not in A.metadata:A.metadata[D]={}
	if E:
		G=A.output_dir/f"{B.stem}.dtlx-report.txt"
		if _run_dtlx_analyze(A,B,G):A.metadata[D]['report']=str(G)
	if F:
		C=A.output_dir/f"{B.stem}.dtlx-optimized.apk"
		if _run_dtlx_optimize(A,B,C):A.metadata[D]['optimized_apk']=str(C);A.set_current_apk(C);A.log(f"dtlx: pipeline will continue with {C}")
		else:A.log('dtlx: optimization failed, pipeline will continue with original APK')