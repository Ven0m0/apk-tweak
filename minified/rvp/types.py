from __future__ import annotations
_A=False
from typing import TYPE_CHECKING
from typing import Any
from typing import TypedDict
if TYPE_CHECKING:from pathlib import Path
class RkPairipOptions(TypedDict,total=_A):apktool_mode:bool;merge_skip:bool;dex_repair:bool;corex_hook:bool;anti_split:bool
class ToolPaths(TypedDict,total=_A):revanced_cli:str;patches:str;revanced_integrations:str;apktool_path:str;zipalign_path:str
class PipelineOptions(TypedDict,total=_A):dtlx_analyze:bool;dtlx_optimize:bool;revanced_optimize:bool;revanced_debloat:bool;revanced_minify:bool;revanced_patch_ads:bool;revanced_include_patches:list[str];revanced_exclude_patches:list[str];revanced_exclusive:bool;revanced_patches:list[str|dict[str,Any]];lspatch_modules:list[str];discord_keystore:Path|str;discord_keystore_pass:str;discord_version:str;discord_patches:list[str];whatsapp_ab_tests:bool;whatsapp_timeout:int;whatsapp_temp_dir:str;optimize_images:bool;optimize_audio:bool;target_dpi:str;rkpairip:RkPairipOptions;tools:ToolPaths;debloat_patterns:list[str];minify_patterns:list[str]