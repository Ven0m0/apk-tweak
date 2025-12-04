"""APK optimization utilities using apktool, zipalign, and aapt2."""

from __future__ import annotations

import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .context import Context
from .utils import run_command

# Ad patterns adapted from ApkPatcher/Patch/Ads_Patch.py
AD_PATTERNS = [
  (
    r'"(com.google.android.play.core.appupdate.protocol.IAppUpdateService|Theme.Dialog.Alert|com.google.android.play.core.install.BIND_UPDATE_SERVICE)"',
    r'""',
    "Update Disable",
  ),
  (
    r'(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->(.*(load|show).*)\([^)]*\)V)|(invoke(?!.*(close|Deactiv|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop|Throw)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->(request.*|(.*(activat|Banner|build|Event|exec|header|html|initAd|initi|JavaScript|Interstitial|load|log|MetaData|metri|Native|onAd|propert|report|response|Rewarded|show|trac|url|(fetch|refresh|render|video)Ad).*)|.*Request)\([^)]*\)V)|(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->((.*(Banner|initAd|Interstitial|load|Native|onAd|Rewarded|show|(fetch|refresh|render|request|video)Ad).*))\([^)]*\)V)|invoke-.*\{.*\}, L[^;]+;->(loadAd|requestNativeAd|showInterstitial|fetchad|fetchads|onadloaded|requestInterstitialAd|showAd|loadAds|AdRequest|requestBannerAd|loadNextAd|createInterstitialAd|setNativeAd|loadBannerAd|loadNativeAd|loadRewardedAd|loadRewardedInterstitialAd|loadAds|loadAdViewAd|showInterstitialAd|shownativead|showbannerad|showvideoad|onAdFailedToLoad)\([^)]*\)V|invoke-[^{]+ \{[^\}]*\}, Lcom[^;]+;->requestInterstitialAd\([^)]*\)V|invoke-[^{]+ \{[^\}]*\}, Lcom[^;]+;->loadAds\([^)]*\)V|invoke-[^{]+ \{[^\}]*\}, Lcom[^;]+;->loadAd\([^)]*\)V|invoke-[^{]+ \{[^\}]*\}, Lcom[^;]+;->requestBannerAd\([^)]*\)V|invoke-[^{]+ \{[pv]\d\}, Lcom/facebook[^;]+;->show\([^)]*\)V|invoke-[^{]+ \{[pv]\d\}, Lcom/google[^;]+;->show\([^)]*\)V',
    r'nop',
    "Ads Regex 1",
  ),
  (
    r'(invoke(?!.*(close|Deactiv|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop|Throw)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->(request.*|(.*(activat|Banner|build|Event|exec|header|html|initAd|initi|JavaScript|Interstitial|load|log|MetaData|metri|Native|(can|get|is|has|was)Ad|propert|report|response|Rewarded|show|trac|url|(fetch|refresh|render|video)Ad).*)|.*Request)\([^)]*\)Z[^>]*?)move-result ([pv]\d+)|(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->((.*(Banner|initAd|Interstitial|load|Native|(can|get|has|is|was)Ad|Rewarded|show|(fetch|refresh|render|request|video)Ad).*))\([^)]*\)Z[^>]*?)move-result ([pv]\d+)',
    r'const/4 \9, 0x0',
    "Ads Regex 2",
  ),
  (
    r'(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->(.*(load|show).*)\([^)]*\)Z[^>]*?)move-result ([pv]\d+)',
    r'const/4 \6, 0x0',
    "Ads Regex 3",
  ),
  (
    r'(\.method\s(public|private|static)\s\b(?!\babstract|native\b)[^(]*?loadAd\([^)]*\)V)',
    r'\1\n\treturn-void',
    "Ads Regex 4",
  ),
  (
    r'(\.method\s(public|private|static)\s\b(?!\babstract|native\b)[^(]*?loadAd\([^)]*\)Z)',
    r'\1\n\tconst/4 v0, 0x0\n\treturn v0',
    "Ads Regex 5",
  ),
  (
    r'(invoke[^{]+ \{[^\}]*\}, L[^(]*loadAd\([^)]*\)[VZ])|(invoke[^{]+ \{[^\}]*\}, L[^(]*gms.*\>(loadUrl|loadDataWithBaseURL|requestInterstitialAd|showInterstitial|showVideo|showAd|loadData|onAdClicked|onAdLoaded|isLoading|loadAds|AdLoader|AdRequest|AdListener|AdView)\([^)]*\)V)',
    r'#',
    "Ads Regex 6",
  ),
  (
    r'\.method [^(]*(loadAd|requestNativeAd|showInterstitial|fetchad|fetchads|onadloaded|requestInterstitialAd|showAd|loadAds|AdRequest|requestBannerAd|loadNextAd|createInterstitialAd|setNativeAd|loadBannerAd|loadNativeAd|loadRewardedAd|loadRewardedInterstitialAd|loadAds|loadAdViewAd|showInterstitialAd|shownativead|showbannerad|showvideoad|onAdFailedToLoad)\([^)]*\)V\s+\.locals \d+[\s\S]*?\.end method',
    r'#',
    "Ads Regex 7",
  ),
  (
    r'"ca-app-pub-\d{16}/\d{10}"',
    r'"ca-app-pub-0000000000000000/0000000000"',
    "Ads Regex 8",
  ),
  (
    r'"(http.*|//.*)(61.145.124.238|-ads.|.ad.|.ads.|.analytics.localytics.com|.mobfox.com|.mp.mydas.mobi|.plus1.wapstart.ru|.scorecardresearch.com|.startappservice.com|/ad.|/ads|ad-mail|ad.*_logging|ad.api.kaffnet.com|adc3-launch|adcolony|adinformation|adkmob|admax|admob|admost|adsafeprotected|adservice|adtag|advert|adwhirl|adz.wattpad.com|alta.eqmob.com|amazon-*ads|amazon.*ads|amobee|analytics|applovin|applvn|appnext|appodeal|appsdt|appsflyer|burstly|cauly|cloudfront|com.google.android.gms.ads.identifier.service.START|crashlytics|crispwireless|doubleclick|dsp.batmobil.net|duapps|dummy|flurry|gad|getads|google.com/dfp|googleAds|googleads|googleapis.*.ad-*|googlesyndication|googletagmanager|greystripe|gstatic|inmobi|inneractive|jumptag|live.chartboost.com|madnet|millennialmedia|moatads|mopub|native_ads|pagead|pubnative|smaato|supersonicads|tapas|tapjoy|unityads|vungle|zucks).*"',
    r'"="',
    "Ads Regex 9",
  ),
  (
    r'"(http.*|//.*)(61\.145\.124\.238|/2mdn\.net|-ads\.|\.5rocks\.io|\.ad\.|\.adadapted|\.admitad\.|\.admost\.|\.ads\.|\.aerserv\.|\.airpush\.|\.batmobil\.|\.chartboost\.|\.cloudmobi\.|\.conviva\.|\.dov-e\.com|\.fyber\.|\.mng-ads\|\.mydas\.|\.predic\.|\.talkingdata\.|\.tapdaq\.|\.tele\.fm|\.unity3d\.|\.unity\.|\.wapstart\.|\.xdrig\.|\.zapr\.|\/ad\.|\/ads|a4\.tl|accengage|ad4push|ad4screen|ad-mail|ad\..*_logging|ad\.api\.kaffnet\.|ad\.cauly\.co\.|adbuddiz|adc3-launch|adcolony|adfurikun|adincube|adinformation|adkmob|admax\.|admixer|admob|admost|ads\.mdotm\.|adsafeprotected|adservice|adsmogo|adsrvr|adswizz|adtag|adtech\.de|advert|adwhirl|adz\.wattpad\.|alimama\.|alta\.eqmob\.|amazon-.*ads|amazon\..*ads|amobee|analytics|anvato|appboy|appbrain|applovin|applvn|appmetrica|appnext|appodeal|appsdt|appsflyer|apsalar|avocarrot|axonix|banners-slb\.mobile\.yandex\.net|banners\.mobile\.yandex\.net|brightcove\.|burstly|cauly|cloudfront|cmcm\.|com\.google\.android\.gms\.ads\.identifier\.service\.START|comscore|contextual\.media\.net|crashlytics|crispwireless|criteo\.|dmtry\.|doubleclick|duapps|dummy|flurry|fwmrm|gad|getads|gimbal|glispa|google\.com\/dfp|googleAds|googleads|googleapis\..*\.ad-.*|googlesyndication|googletagmanager|greystripe|gstatic|heyzap|hyprmx|iasds01|inmobi|inneractive|instreamatic|integralads|jumptag|jwpcdn|jwpltx|jwpsrv|kochava|localytics|madnet|mapbox|mc\.yandex\.ru|media\.net|metrics\.|millennialmedia|mixpanel|mng-ads\.com|moat\.|moatads|mobclix|mobfox|mobpowertech|moodpresence|mopub|native_ads|nativex\.|nexage\.|ooyala|openx\.|pagead|pingstart|prebid|presage\.io|pubmatic|pubnative|rayjump|saspreview|scorecardresearch|smaato|smartadserver|sponsorpay|startappservice|startup\.mobile\.yandex\.net|statistics\.videofarm\.daum\.net|supersonicads|taboola|tapas|tapjoy|tapylitics|target\.my\.com|teads\.|umeng|unityads|vungle|zucks).*"',
    r'"127.0.0.1"',
    "Ads Regex 10",
  ),
  (
    r'(invoke-interface \{[^\}]*\}, Lcom/google/android/vending/licensing/Policy;->allowAccess\(\)Z[^>]*?\s+)move-result ([pv]\d+)',
    r'\1const/4 \2, 0x1',
    "Bypass Client-Side LVL (allowAccess)",
  ),
  (
    r'(\.method [^(]*connectToLicensingService\(\)V\s+.locals \d+)[\s\S]*?(\s+return-void\n.end method)',
    r'\1\2',
    "connectToLicensingService",
  ),
  (
    r'(\.method [^(]*initializeLicenseCheck\(\)V\s+.locals \d+)[\s\S]*?(\s+return-void\n.end method)',
    r'\1\2',
    "initializeLicenseCheck",
  ),
  (
    r'(\.method [^(]*processResponse\(ILandroid/os/Bundle;\)V\s+.locals \d+)[\s\S]*?(\s+return-void\n.end method)',
    r'\1\2',
    "processResponse",
  ),
]


def decompile_apk(apk: Path, output_dir: Path, ctx: Context) -> Path:
  """
  Decompile APK using apktool.

  Args:
      apk: Path to APK file.
      output_dir: Directory for decompiled output.
      ctx: Pipeline context for logging.

  Returns:
      Path: Directory containing decompiled APK.
  """
  decompiled_dir = output_dir / f"{apk.stem}_decompiled"
  apktool = ctx.options.get("apktool_path", "apktool")
  cmd = [str(apktool), "d", str(apk), "-o", str(decompiled_dir), "-f"]
  ctx.log(f"optimizer: Decompiling {apk.name}")
  run_command(cmd, ctx)
  return decompiled_dir


def debloat_apk(decompiled_dir: Path, ctx: Context) -> None:
  """
  Remove bloatware from decompiled APK.

  Args:
      decompiled_dir: Directory containing decompiled APK.
      ctx: Pipeline context for logging and options.
  """
  ctx.log("optimizer: Starting debloat process")
  # Get debloat patterns from options
  debloat_patterns = ctx.options.get("debloat_patterns", [])
  if not debloat_patterns:
    ctx.log("optimizer: No debloat patterns specified, skipping")
    return
  removed_count = 0
  # Remove files matching debloat patterns (O(n*m) where n=files, m=patterns)
  for pattern in debloat_patterns:
    matches = list(decompiled_dir.rglob(pattern))
    for match in matches:
      if match.is_file():
        ctx.log(f"optimizer: Removing {match.relative_to(decompiled_dir)}")
        match.unlink()
        removed_count += 1
      elif match.is_dir():
        ctx.log(f"optimizer: Removing directory {match.relative_to(decompiled_dir)}")
        shutil.rmtree(match)
        removed_count += 1
  ctx.log(f"optimizer: Debloat complete - removed {removed_count} items")


def minify_resources(decompiled_dir: Path, ctx: Context) -> None:
  """
  Minify APK resources (remove unused resources).

  Args:
      decompiled_dir: Directory containing decompiled APK.
      ctx: Pipeline context for logging.
  """
  ctx.log("optimizer: Starting resource minification")
  # Remove unused resource files
  # Common unused resources: drawable-xxxhdpi, raw audio, etc.
  minify_patterns = ctx.options.get(
    "minify_patterns",
    [
      "res/drawable-xxxhdpi/*",  # Extra high DPI (often unnecessary)
      "res/raw/*.mp3",  # Large audio files
      "res/raw/*.wav",
      "assets/unused/*",  # Unused assets
    ],
  )
  removed_count = 0
  removed_size = 0
  for pattern in minify_patterns:
    matches = list(decompiled_dir.rglob(pattern))
    for match in matches:
      if match.is_file():
        size = match.stat().st_size
        ctx.log(f"optimizer: Removing {match.relative_to(decompiled_dir)} ({size} bytes)")
        match.unlink()
        removed_count += 1
        removed_size += size
  ctx.log(f"optimizer: Minification complete - removed {removed_count} files ({removed_size} bytes)")


def _apply_patch_to_file(file_path: Path, patterns: list[tuple[str, str, str]], ctx: Context) -> int:
  """Apply patches to a single file. Helper for patch_ads."""
  try:
    # Use 'ignore' errors to match original script behavior
    content = file_path.read_text(encoding="utf-8", errors="ignore")
    original_content = content
    applied_count = 0

    for pattern, replacement, _ in patterns:
      # Use re.sub directly
      content = re.sub(pattern, replacement, content)

    if content != original_content:
      file_path.write_text(content, encoding="utf-8", errors="ignore")
      applied_count = 1  # Mark as patched

    return applied_count
  except Exception as e:
    ctx.log(f"optimizer: Error patching {file_path.name}: {e}")
    return 0


def patch_ads(decompiled_dir: Path, ctx: Context) -> None:
  """
  Apply regex-based ad patching to smali files.

  Args:
      decompiled_dir: Directory containing decompiled APK.
      ctx: Pipeline context.
  """
  ctx.log("optimizer: Starting regex-based ad patching")

  # Find all smali files
  smali_files = list(decompiled_dir.rglob("*.smali"))
  if not smali_files:
    ctx.log("optimizer: No smali files found")
    return

  ctx.log(f"optimizer: Scanning {len(smali_files)} smali files...")

  # Pre-compile regex patterns if possible, but the patterns list has descriptions
  # We'll just pass the raw patterns list to the helper for simplicity/compatibility
  total_patched = 0

  # Use ThreadPool for performance (IO boundish, but regex is CPU)
  # O(n) scan of files
  with ThreadPoolExecutor() as executor:
    futures = []
    for smali_file in smali_files:
      futures.append(executor.submit(_apply_patch_to_file, smali_file, AD_PATTERNS, ctx))

    for future in futures:
      total_patched += future.result()

  ctx.log(f"optimizer: Ad patching complete - modified {total_patched} files")


def recompile_apk(decompiled_dir: Path, output_apk: Path, ctx: Context) -> None:
  """
  Recompile APK using apktool.

  Args:
      decompiled_dir: Directory containing decompiled APK.
      output_apk: Path for output APK.
      ctx: Pipeline context for logging.
  """
  apktool = ctx.options.get("apktool_path", "apktool")
  cmd = [str(apktool), "b", str(decompiled_dir), "-o", str(output_apk)]
  ctx.log(f"optimizer: Recompiling APK to {output_apk.name}")
  run_command(cmd, ctx)


def zipalign_apk(input_apk: Path, output_apk: Path, ctx: Context) -> None:
  """
  Optimize APK using zipalign.

  Args:
      input_apk: Path to input APK.
      output_apk: Path for aligned APK.
      ctx: Pipeline context for logging.
  """
  zipalign = ctx.options.get("zipalign_path", "zipalign")
  # -f = force overwrite, -v = verbose, 4 = alignment in bytes
  cmd = [str(zipalign), "-f", "-v", "4", str(input_apk), str(output_apk)]
  ctx.log(f"optimizer: Running zipalign on {input_apk.name}")
  run_command(cmd, ctx)


def optimize_apk(
  input_apk: Path,
  output_apk: Path,
  ctx: Context,
  debloat: bool = True,
  minify: bool = True,
) -> None:
  """
  Complete APK optimization pipeline.

  Args:
      input_apk: Path to input APK.
      output_apk: Path for optimized APK.
      ctx: Pipeline context.
      debloat: Enable debloating.
      minify: Enable resource minification.
  """
  ctx.log("optimizer: Starting optimization pipeline")
  work_dir = ctx.work_dir / "optimizer"
  work_dir.mkdir(parents=True, exist_ok=True)

  # Check if ad patching is enabled via options
  patch_ads_enabled = ctx.options.get("revanced_patch_ads", False)

  # Step 1: Decompile
  decompiled_dir = decompile_apk(input_apk, work_dir, ctx)

  # Step 2: Debloat (if enabled)
  if debloat:
    debloat_apk(decompiled_dir, ctx)

  # Step 3: Minify resources (if enabled)
  if minify:
    minify_resources(decompiled_dir, ctx)

  # Step 4: Ad Patching (if enabled)
  if patch_ads_enabled:
    patch_ads(decompiled_dir, ctx)

  # Step 5: Recompile
  temp_apk = work_dir / f"{input_apk.stem}_recompiled.apk"
  recompile_apk(decompiled_dir, temp_apk, ctx)

  # Step 6: Zipalign
  zipalign_apk(temp_apk, output_apk, ctx)
  ctx.log(f"optimizer: Optimization complete - {output_apk}")
