from __future__ import annotations
_B='__path__'
_A=None
import importlib,pkgutil,sys
from collections.abc import Callable
from pathlib import Path
from.import engines as engines_pkg,plugins as plugins_pkg
from.context import Context
from.types import PipelineOptions
from.validators import validate_apk_path,validate_output_dir
EngineFn=Callable[[Context],_A]
PluginHandler=Callable[[Context,str],_A]
class _ModuleCache:
	def __init__(A):A._engines=_A;A._plugins=_A
	def get_engines(A):
		if A._engines is not _A:return A._engines
		B={}
		if hasattr(engines_pkg,_B):
			for(E,C,E)in pkgutil.iter_modules(engines_pkg.__path__):
				try:
					F=f"{engines_pkg.__name__}.{C}";D=importlib.import_module(F)
					if hasattr(D,'run')and callable(D.run):B[C]=D.run
				except(ImportError,AttributeError)as G:print(f"[rvp] WARN: Engine '{C}' load fail: {G}",file=sys.stderr)
		A._engines=B;return B
	def get_plugins(A):
		if A._plugins is not _A:return A._plugins
		B=[]
		if hasattr(plugins_pkg,_B):
			for(E,D,E)in pkgutil.iter_modules(plugins_pkg.__path__):
				try:
					F=f"{plugins_pkg.__name__}.{D}";C=importlib.import_module(F)
					if hasattr(C,'handle_hook')and callable(C.handle_hook):B.append(C.handle_hook)
				except(ImportError,AttributeError)as G:print(f"[rvp] WARN: Plugin '{D}' load fail: {G}",file=sys.stderr)
		A._plugins=B;return B
_module_cache=_ModuleCache()
def get_engines():return _module_cache.get_engines()
def load_plugins():return _module_cache.get_plugins()
def dispatch_hooks(ctx,stage,handlers):
	A=stage
	for B in handlers:
		try:B(ctx,A)
		except(RuntimeError,ValueError,OSError)as C:ctx.log(f"Plugin hook error at '{A}': {C}",level=40)
def run_pipeline(input_apk,output_dir,engines,options=_A):
	H=engines;G=options;F=True;D=output_dir;C=input_apk;validate_apk_path(C);validate_output_dir(D);G=G or{};I=D/'tmp';I.mkdir(parents=F,exist_ok=F);D.mkdir(parents=F,exist_ok=F);A=Context(work_dir=I,input_apk=C,output_dir=D,engines=H,options=G);A.log(f"Starting pipeline for: {C}");A.set_current_apk(C);J=get_engines();E=load_plugins();dispatch_hooks(A,'pre_pipeline',E)
	for B in H:
		if B not in J:A.log(f"⚠️ Skipping unknown engine: {B}");continue
		dispatch_hooks(A,f"pre_engine:{B}",E);A.log(f"Running engine: {B}")
		try:J[B](A)
		except(OSError,ValueError,RuntimeError)as K:A.log(f"❌ Engine {B} failed: {K}");raise RuntimeError(f"Engine {B} failed")from K
		dispatch_hooks(A,f"post_engine:{B}",E)
	dispatch_hooks(A,'post_pipeline',E);A.log(f"Pipeline finished. Final APK: {A.current_apk}");return A