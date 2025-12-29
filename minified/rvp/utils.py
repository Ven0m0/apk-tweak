from __future__ import annotations
_C=None
_B=False
_A=True
import shutil,subprocess
from pathlib import Path
from.context import Context
TIMEOUT_CLONE=120
TIMEOUT_PATCH=900
TIMEOUT_ANALYZE=300
TIMEOUT_OPTIMIZE=600
TIMEOUT_BUILD=1200
def require_input_apk(ctx):
	A=ctx.current_apk or ctx.input_apk
	if not A:raise ValueError('No input APK found in context')
	return A
def run_command(cmd,ctx,cwd=_C,check=_A,timeout=_C,env=_C):
	H=check;E=timeout;B=cmd;A=ctx;A.log(f"EXEC: {' '.join(str(A)for A in B)}")
	if E:A.log(f"  Timeout: {E}s")
	try:
		with subprocess.Popen(B,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=_A,cwd=cwd,env=env,bufsize=8192,encoding='utf-8',errors='replace')as C:
			if C.stdout:
				D=[]
				for J in C.stdout:
					I=J.strip()
					if I:
						D.append(I)
						if len(D)>=10:
							for F in D:A.log(f"  {F}")
							D=[]
				for F in D:A.log(f"  {F}")
		try:G=C.wait(timeout=E)
		except subprocess.TimeoutExpired:C.kill();C.wait();A.log(f"ERR: Command timed out after {E}s");raise
		if H and G!=0:raise subprocess.CalledProcessError(G,B)
		return subprocess.CompletedProcess(B,G)
	except subprocess.TimeoutExpired:raise
	except(OSError,ValueError)as K:
		A.log(f"ERR: Command failed: {K}")
		if H:raise
		return subprocess.CompletedProcess(B,1)
def check_dependencies(required):A=[A for A in required if not shutil.which(A)];return not A,A
def clone_repository(url,target_dir,ctx,timeout=TIMEOUT_CLONE):
	D=timeout;B=target_dir;A=ctx
	if B.exists():A.log(f"Repository already cloned at {B}, skipping");return _A
	A.log(f"Cloning repository from {url}")
	try:subprocess.run(['git','clone',url,str(B)],capture_output=_A,text=_A,timeout=D,check=_A);A.log(f"Repository cloned successfully to {B}");return _A
	except subprocess.TimeoutExpired:A.log(f"ERR: Clone timed out after {D}s");return _B
	except subprocess.CalledProcessError as C:A.log(f"ERR: Clone failed: {C.stderr or C.stdout}");return _B
	except OSError as C:A.log(f"ERR: Clone error: {C}");return _B
def find_latest_apk(directory):
	A=directory
	if not A.exists():return
	B=list(A.glob('*.apk'))
	if not B:return
	return max(B,key=lambda p:p.stat().st_mtime)
def build_tool_command(tool_name,ctx,jar_key,default_jar,base_args=_C):
	C=base_args;B=tool_name
	if shutil.which(B):A=[B]
	else:D=ctx.options.get('tools',{});E=Path(D.get(jar_key,default_jar));A=['java','-jar',str(E)]
	if C:A.extend(C)
	return A
def run_cli_tool(cmd,ctx,tool_name,output_path,timeout=TIMEOUT_PATCH):
	C=output_path;B=tool_name;A=ctx;A.log(f"{B}: running CLI → {C.name}")
	try:
		D=run_command(cmd,A,timeout=timeout,check=_B)
		if D.returncode==0 and C.exists():A.log(f"{B}: CLI execution successful");return _A
		A.log(f"{B}: CLI failed (exit code: {D.returncode})");return _B
	except(OSError,subprocess.SubprocessError)as E:A.log(f"{B}: CLI error: {E}");return _B
def validate_and_require_dependencies(ctx,required,tool_name,install_msg,fallback=_B):
	B=ctx;A=tool_name;D,C=check_dependencies(required)
	if not D:
		B.log(f"{A}: Missing dependencies: {', '.join(C)}");B.log(f"{A}: {install_msg}")
		if fallback:B.log(f"{A}: Falling back to stub/alternative mode");return _B
		raise FileNotFoundError(f"{A} dependencies missing: {C}")
	return _A