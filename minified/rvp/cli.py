from __future__ import annotations
_L='rkpairip_anti_split'
_K='rkpairip_dex_repair'
_J='rkpairip_merge_skip'
_I='anti_split'
_H='corex_hook'
_G='dex_repair'
_F='merge_skip'
_E='apktool_mode'
_D='rkpairip'
_C=True
_B=None
_A=False
import argparse,dataclasses,logging,sys
from pathlib import Path
from typing import Any,cast
from.config import Config
from.core import run_pipeline
from.types import PipelineOptions
def _build_config_options(cfg):B=dataclasses.asdict(cfg);C={'input_apk','output_dir','engines'};A={A:B for(A,B)in B.items()if A not in C};D={'rkpairip_apktool_mode':_E,_J:_F,_K:_G,'rkpairip_corex_hook':_H,_L:_I};A[_D]={C:A.pop(B)for(B,C)in D.items()};A['tools']={'revanced_cli':A.pop('revanced_cli_path'),'patches':A.pop('revanced_patches_path'),'revanced_integrations':A.pop('revanced_integrations_path')};return cast(PipelineOptions,A)
def _build_default_options():return{_D:{_E:_A,_F:_A,_G:_A,_H:_A,_I:_A}}
def _apply_flag_overrides(options,args):
	H='whatsapp_ab_tests';G='dtlx_optimize';F='dtlx_analyze';C='android_builder';A=args;B=cast(dict[str,Any],options);I={F:(F,_B),G:(G,_B),'patch_ads':('revanced_patch_ads',_B)}
	for(D,(E,K))in I.items():
		if getattr(A,D,_A):B[E]=_C
	J={'rkpairip_apktool':_E,_J:_F,_K:_G,'rkpairip_corex':_H,_L:_I};B.setdefault(_D,{})
	for(D,E)in J.items():
		if getattr(A,D,_A):B[_D][E]=_C
	if A.discord_keystore:B['discord_keystore']=A.discord_keystore
	if A.discord_keystore_pass:B['discord_keystore_pass']=A.discord_keystore_pass
	if A.discord_version:B['discord_version']=A.discord_version
	if A.discord_patches:B['discord_patches']=A.discord_patches
	if hasattr(A,'luniume_patches')and A.luniume_patches:B['revanced_patches']=A.luniume_patches
	if hasattr(A,'luniume_modules')and A.luniume_modules:B['lspatch_modules']=A.luniume_modules
	if hasattr(A,'luniume_exclusive')and A.luniume_exclusive:B['revanced_exclusive']=_C
	if hasattr(A,H):B[H]=A.whatsapp_ab_tests
	if A.whatsapp_timeout:B['whatsapp_timeout']=A.whatsapp_timeout
	B.setdefault(C,{})
	if A.android_source_dir:B[C]['android_source_dir']=A.android_source_dir
	if A.android_build_task:B[C]['android_build_task']=A.android_build_task
	if A.android_output_pattern:B[C]['android_output_pattern']=A.android_output_pattern
	if A.optimize_images:B['optimize_images']=_C
	if A.optimize_audio:B['optimize_audio']=_C
	if A.target_dpi:B['target_dpi']=A.target_dpi
def setup_logging(verbose):A=logging.DEBUG if verbose else logging.INFO;logging.basicConfig(level=A,format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',datefmt='%H:%M:%S',handlers=[logging.StreamHandler(sys.stdout)])
def parse_args(argv=_B):C='+';B='store_true';A=argparse.ArgumentParser(prog='rvp',description='APK Tweak Pipeline');A.add_argument('apk',nargs='?',help='Input APK path');A.add_argument('-c','--config',help='Path to config JSON file');A.add_argument('-o','--out',help='Output directory');A.add_argument('-e','--engine',action='append',help='Engines to run');A.add_argument('-v','--verbose',action=B,help='Enable debug logging');A.add_argument('--dtlx-analyze',action=B,help='Enable DTL-X analysis');A.add_argument('--dtlx-optimize',action=B,help='Enable DTL-X optimization');A.add_argument('--patch-ads',action=B,help='Enable regex-based ad patching');A.add_argument('--rkpairip-apktool',action=B,help='RKPairip: Use ApkTool mode');A.add_argument('--rkpairip-merge-skip',action=B,help='RKPairip: Enable merge skip mode');A.add_argument('--rkpairip-dex-repair',action=B,help='RKPairip: Enable DEX repair');A.add_argument('--rkpairip-corex',action=B,help='RKPairip: Enable CoreX hook (Unity/Flutter)');A.add_argument('--rkpairip-anti-split',action=B,help='RKPairip: Enable anti-split merge');A.add_argument('--discord-keystore',help='Discord: Path to custom signing keystore');A.add_argument('--discord-keystore-pass',help='Discord: Keystore password (default: android)');A.add_argument('--discord-version',help='Discord: Target Discord version (default: auto)');A.add_argument('--discord-patches',nargs=C,help='Discord: Custom patches to apply');A.add_argument('--luniume-patches',nargs=C,help='[DEPRECATED] Use revanced engine with --revanced-patches instead');A.add_argument('--luniume-modules',nargs=C,help='[DEPRECATED] Use lspatch engine with --lspatch-modules instead');A.add_argument('--luniume-exclusive',action=B,help='[DEPRECATED] Use revanced engine with --revanced-exclusive instead');A.add_argument('--whatsapp-ab-tests',action=B,default=_C,help='WhatsApp: Enable A/B testing features (default: True)');A.add_argument('--whatsapp-timeout',type=int,help='WhatsApp: Patching timeout in seconds (default: 1200)');A.add_argument('--android-source-dir',help='Builder: Path to the root of the Android project to compile');A.add_argument('--android-build-task',help='Builder: Gradle task to execute (default: assembleRelease)');A.add_argument('--android-output-pattern',help='Builder: Glob pattern to find the output APK/AAB (default: **/*release.apk)');A.add_argument('--optimize-images',action=B,help='Media: Optimize PNG and JPEG images');A.add_argument('--optimize-audio',action=B,help='Media: Optimize MP3 and OGG audio files');A.add_argument('--target-dpi',help='Media: Target DPI(s) to keep, comma-separated (e.g., xhdpi,xxhdpi)');return A.parse_args(argv)
def main(argv=_B):
	A=parse_args(argv);setup_logging(A.verbose);C=logging.getLogger('rvp.cli');B=_B
	if A.config:
		try:B=Config.load_from_file(Path(A.config))
		except(FileNotFoundError,OSError)as D:C.error(f"Config file error: {D}");return 1
		except ValueError as D:C.error(f"Invalid config format: {D}");return 1
	G=A.apk or(B.input_apk if B else _B)
	if not G:C.error('Input APK is required via argument or config file.');return 1
	F=Path(G)
	if not F.exists():C.error(f"Input APK not found: {F}");return 1
	I=Path(A.out)if A.out else Path(B.output_dir if B else'out');E=A.engine
	if not E and B:E=B.engines
	if not E:E=['revanced']
	H=_build_config_options(B)if B else _build_default_options();_apply_flag_overrides(H,A)
	try:run_pipeline(F,I,E,H)
	except(OSError,ValueError,RuntimeError)as D:
		C.error(f"Pipeline failed: {D}")
		if A.verbose:import traceback as J;J.print_exc()
		return 1
	return 0
if __name__=='__main__':raise SystemExit(main())