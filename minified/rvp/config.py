from __future__ import annotations
_C='utf-8'
_B=True
_A=False
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
try:
	from typing import Any,TextIO;import orjson
	def _load_json(file_handle):return orjson.loads(file_handle.read())
	def _dump_json(data,file_handle):A=orjson.dumps(data,option=orjson.OPT_INDENT_2|orjson.OPT_SORT_KEYS);file_handle.write(A.decode(_C))
except ImportError:
	import json;from typing import Any;from typing import TextIO
	def _load_json(file_handle):return json.load(file_handle)
	def _dump_json(data,file_handle):json.dump(data,file_handle,indent=2,sort_keys=_B)
@dataclass
class Config:
	input_apk:str|None=None;output_dir:str='out';engines:list[str]=field(default_factory=lambda:['revanced']);dtlx_analyze:bool=_A;dtlx_optimize:bool=_A;revanced_cli_path:str='revanced-cli.jar';revanced_patch_bundles:list[str]=field(default_factory=list);revanced_integrations_path:str='integrations.apk';revanced_optimize:bool=_B;revanced_debloat:bool=_B;revanced_minify:bool=_B;revanced_patch_ads:bool=_A;revanced_patches:list[str|dict[str,Any]]=field(default_factory=list);revanced_include_patches:list[str]=field(default_factory=list);revanced_exclude_patches:list[str]=field(default_factory=list);debloat_patterns:list[str]=field(default_factory=lambda:['*/admob/*','*/google/ads/*','*/facebook/ads/*','*/mopub/*','*/applovin/*','*/unity3d/ads/*','*/vungle/*','*/chartboost/*','*/inmobi/*','*/flurry/*','assets/extensions/ads/*','assets/extensions/search/*','*/analytics/*','*/crashlytics/*','*/firebase/analytics/*','*/firebase/crashlytics/*','*/google/firebase/analytics/*','*/adjust/*','*/branch/*','*/appsflyer/*','*/kochava/*','LICENSE_UNICODE','LICENSE_OFL','LICENSE.txt','NOTICE.txt','THIRD_PARTY_LICENSES','*/licenses/*','META-INF/*','car-app-api.level','*.properties','*/build-data.properties','com/google/android/libraries/phonenumbers/data/PhoneNumberMetadataProto_A[CDEFGH]*','com/google/android/libraries/phonenumbers/data/PhoneNumberMetadataProto_[B-Z]*','com/google/android/libraries/phonenumbers/data/PhoneNumberAlternateFormatsProto_*','org/joda/time/format/messages_*.properties','org/joda/time/tz/data/Africa/*','org/joda/time/tz/data/America/*','org/joda/time/tz/data/Antarctica/*','org/joda/time/tz/data/Asia/*','org/joda/time/tz/data/Atlantic/*','org/joda/time/tz/data/Australia/*','org/joda/time/tz/data/Indian/*','org/joda/time/tz/data/Pacific/*','*/gms/*','*/play/core/*','*/android/gms/ads/*','*/android/gms/analytics/*','*/twitter/sdk/*','*/linkedin/platform/*','*/snapchat/kit/*','assets/unused_*','assets/debug/*','assets/test/*']);minify_patterns:list[str]=field(default_factory=lambda:['res/drawable-xxxhdpi/*','res/drawable-xxhdpi/*','res/raw/*.mp3','res/raw/*.wav','res/raw/*.ogg','res/raw/*.m4a','assets/kazoo/*','assets/images/*.png','assets/images/*.jpg','assets/backgrounds/*','assets/splash/*','res/raw/*.mp4','res/raw/*.webm','assets/video/*','res/font/*-bold.ttf','res/font/*-light.ttf','assets/fonts/*-thin.ttf','res/raw/unused_*','assets/unused/*']);apktool_path:str='apktool';zipalign_path:str='zipalign';rkpairip_apktool_mode:bool=_A;rkpairip_merge_skip:bool=_A;rkpairip_dex_repair:bool=_A;rkpairip_corex_hook:bool=_A;rkpairip_anti_split:bool=_A;revanced_patches_path:str='patches.jar'
	@classmethod
	def load_from_file(B,path):
		A=path
		if not A.exists():raise FileNotFoundError(f"Config file not found: {A}")
		with open(A,encoding=_C)as C:D=_load_json(C);return B(**D)
	def save_to_file(A,path):
		from dataclasses import asdict as B;path.parent.mkdir(parents=_B,exist_ok=_B)
		with open(path,'w',encoding=_C)as C:D=B(A);_dump_json(D,C)