"""
Ad and licensing validation bypass patterns.

Regex patterns adapted from ApkPatcher for removing ads and bypassing
licensing checks in smali files.
"""

from __future__ import annotations

import re
from typing import Pattern

# Type alias for pattern tuples: (compiled_pattern, replacement, description)
AdPattern = tuple[Pattern[str], str, str]

# ⚡ Perf: Pre-compile regex patterns at module load time
# This prevents re-compilation on every file iteration (50-70% speedup)
_RAW_PATTERNS: list[tuple[str, str, str]] = [
  (
    r'"(com.google.android.play.core.appupdate.protocol.'
    r"IAppUpdateService|Theme.Dialog.Alert|"
    r'com.google.android.play.core.install.BIND_UPDATE_SERVICE)"',
    r'""',
    "Update Disable",
  ),
  (
    r"(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|"
    r"remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|"
    r"adsdk|aerserv|appbrain|applovin|appodeal|appodealx|"
    r"appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|"
    r"hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|"
    r"mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|"
    r"presage|smaato|smartadserver|snap/adkit|snap/appadskit|"
    r"startapp|taboola|tapjoy|tappx|vungle)/[^;]+;"
    r"->(.*load|show.*)\([^)]*\)V)|(invoke(?!.*(close|Deactiv|"
    r"Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|"
    r"skip|stop|Throw)).*/(adcolony|admob|ads|adsdk|aerserv|"
    r"appbrain|applovin|appodeal|appodealx|appsflyer|"
    r"bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|"
    r"inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|"
    r"mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|"
    r"smaato|smartadserver|snap/adkit|snap/appadskit|startapp|"
    r"taboola|tapjoy|tappx|vungle)/[^;]+;->(request.*|"
    r"(.*(activat|Banner|build|Event|exec|header|html|initAd|"
    r"initi|JavaScript|Interstitial|load|log|MetaData|metri|"
    r"Native|onAd|propert|report|response|Rewarded|show|trac|url|"
    r"(fetch|refresh|render|video)Ad).*)|.*Request)\([^)]*\)V)|"
    r"(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|"
    r"remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|"
    r"adsdk|aerserv|appbrain|applovin|appodeal|appodealx|"
    r"appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|"
    r"hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|"
    r"mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|"
    r"presage|smaato|smartadserver|snap/adkit|snap/appadskit|"
    r"startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->"
    r"((.*(Banner|initAd|Interstitial|load|Native|onAd|Rewarded|"
    r"show|(fetch|refresh|render|request|video)Ad).*))\([^)]*\)V)|"
    r"invoke-.*\{.*\}, L[^;]+;->(loadAd|requestNativeAd|"
    r"showInterstitial|fetchad|fetchads|onadloaded|"
    r"requestInterstitialAd|showAd|loadAds|AdRequest|"
    r"requestBannerAd|loadNextAd|createInterstitialAd|setNativeAd|"
    r"loadBannerAd|loadNativeAd|loadRewardedAd|"
    r"loadRewardedInterstitialAd|loadAds|loadAdViewAd|"
    r"showInterstitialAd|shownativead|showbannerad|showvideoad|"
    r"onAdFailedToLoad)\([^)]*\)V|invoke-[^{]+ \{[^\}]*\}, "
    r"Lcom[^;]+;->requestInterstitialAd\([^)]*\)V|invoke-[^{]+ "
    r"\{[^\}]*\}, Lcom[^;]+;->loadAds\([^)]*\)V|invoke-[^{]+ "
    r"\{[^\}]*\}, Lcom[^;]+;->loadAd\([^)]*\)V|invoke-[^{]+ "
    r"\{[^\}]*\}, Lcom[^;]+;->requestBannerAd\([^)]*\)V|"
    r"invoke-[^{]+ \{[pv]\d\}, Lcom/facebook[^;]+;->show\([^)]*\)V|"
    r"invoke-[^{]+ \{[pv]\d\}, Lcom/google[^;]+;->show\([^)]*\)V",
    r"nop",
    "Ads Regex 1",
  ),
  (
    r"(invoke(?!.*(close|Deactiv|Destroy|Dismiss|Disabl|error|"
    r"player|remov|expir|fail|hide|skip|stop|Throw)).*/"
    r"(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|"
    r"appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|"
    r"chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|"
    r"mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|"
    r"ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|"
    r"snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;"
    r"->(request.*|(.*(activat|Banner|build|Event|exec|header|html|"
    r"initAd|initi|JavaScript|Interstitial|load|log|MetaData|metri|"
    r"Native|(can|get|is|has|was)Ad|propert|report|response|"
    r"Rewarded|show|trac|url|(fetch|refresh|render|video)Ad).*)|"
    r".*Request)\([^)]*\)Z[^>]*?)move-result ([pv]\d+)|"
    r"(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|"
    r"remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|"
    r"adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|"
    r"bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|"
    r"inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|"
    r"mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|"
    r"smaato|smartadserver|snap/adkit|snap/appadskit|startapp|"
    r"taboola|tapjoy|tappx|vungle)/[^;]+;->((.*(Banner|initAd|"
    r"Interstitial|load|Native|(can|get|has|is|was)Ad|Rewarded|"
    r"show|(fetch|refresh|render|request|video)Ad).*))\([^)]*\)Z"
    r"[^>]*?)move-result ([pv]\d+)",
    r"const/4 \9, 0x0",
    "Ads Regex 2",
  ),
  (
    r"(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|"
    r"remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|"
    r"adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|"
    r"bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|"
    r"inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|"
    r"mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|"
    r"smaato|smartadserver|snap/adkit|snap/appadskit|startapp|"
    r"taboola|tapjoy|tappx|vungle)/[^;]+;->(.*(load|show).*)"
    r"\([^)]*\)Z[^>]*?)move-result ([pv]\d+)",
    r"const/4 \6, 0x0",
    "Ads Regex 3",
  ),
  (
    r"(\.method\s(public|private|static)\s\b(?!\babstract|native\b)"
    r"[^(]*?loadAd\([^)]*\)V)",
    r"\1\n\treturn-void",
    "Ads Regex 4",
  ),
  (
    r"(\.method\s(public|private|static)\s\b(?!\babstract|native\b)"
    r"[^(]*?loadAd\([^)]*\)Z)",
    r"\1\n\tconst/4 v0, 0x0\n\treturn v0",
    "Ads Regex 5",
  ),
  (
    r"(invoke[^{]+ \{[^\}]*\}, L[^(]*loadAd\([^)]*\)[VZ])|"
    r"(invoke[^{]+ \{[^\}]*\}, L[^(]*gms.*\>(loadUrl|"
    r"loadDataWithBaseURL|requestInterstitialAd|showInterstitial|"
    r"showVideo|showAd|loadData|onAdClicked|onAdLoaded|isLoading|"
    r"loadAds|AdLoader|AdRequest|AdListener|AdView)\([^)]*\)V)",
    r"#",
    "Ads Regex 6",
  ),
  (
    r"\.method [^(]*(loadAd|requestNativeAd|showInterstitial|"
    r"fetchad|fetchads|onadloaded|requestInterstitialAd|showAd|"
    r"loadAds|AdRequest|requestBannerAd|loadNextAd|"
    r"createInterstitialAd|setNativeAd|loadBannerAd|loadNativeAd|"
    r"loadRewardedAd|loadRewardedInterstitialAd|loadAds|"
    r"loadAdViewAd|showInterstitialAd|shownativead|showbannerad|"
    r"showvideoad|onAdFailedToLoad)\([^)]*\)V\s+\.locals \d+"
    r"[\s\S]*?\.end method",
    r"#",
    "Ads Regex 7",
  ),
  (
    r'"ca-app-pub-\d{16}/\d{10}"',
    r'"ca-app-pub-0000000000000000/0000000000"',
    "Ads Regex 8",
  ),
  (
    r'"(http.*|//.*)(61.145.124.238|-ads.|.ad.|.ads.|'
    r".analytics.localytics.com|.mobfox.com|.mp.mydas.mobi|"
    r".plus1.wapstart.ru|.scorecardresearch.com|.startappservice.com|"
    r"/ad.|/ads|ad-mail|ad.*_logging|ad.api.kaffnet.com|"
    r"adc3-launch|adcolony|adinformation|adkmob|admax|admob|admost|"
    r"adsafeprotected|adservice|adtag|advert|adwhirl|adz.wattpad.com|"
    r"alta.eqmob.com|amazon-*ads|amazon.*ads|amobee|analytics|"
    r"applovin|applvn|appnext|appodeal|appsdt|appsflyer|burstly|"
    r"cauly|cloudfront|com.google.android.gms.ads.identifier."
    r"service.START|crashlytics|crispwireless|doubleclick|"
    r"dsp.batmobil.net|duapps|dummy|flurry|gad|getads|google.com/dfp|"
    r"googleAds|googleads|googleapis.*.ad-*|googlesyndication|"
    r"googletagmanager|greystripe|gstatic|inmobi|inneractive|"
    r"jumptag|live.chartboost.com|madnet|millennialmedia|moatads|"
    r"mopub|native_ads|pagead|pubnative|smaato|supersonicads|tapas|"
    r'tapjoy|unityads|vungle|zucks).*"',
    r'"="',
    "Ads Regex 9",
  ),
  (
    r'"(http.*|//.*)(61\.145\.124\.238|/2mdn\.net|-ads\.|'
    r"\.5rocks\.io|\.ad\.|\.adadapted|\.admitad\.|\.admost\.|"
    r"\.ads\.|\.aerserv\.|\.airpush\.|\.batmobil\.|\.chartboost\.|"
    r"\.cloudmobi\.|\.conviva\.|\.dov-e\.com|\.fyber\.|\.mng-ads\|"
    r"\.mydas\.|\.predic\.|\.talkingdata\.|\.tapdaq\.|\.tele\.fm|"
    r"\.unity3d\.|\.unity\.|\.wapstart\.|\.xdrig\.|\.zapr\.|\/ad\.|"
    r"/ads|a4\.tl|accengage|ad4push|ad4screen|ad-mail|ad\..*_logging|"
    r"ad\.api\.kaffnet\.|ad\.cauly\.co\.|adbuddiz|adc3-launch|"
    r"adcolony|adfurikun|adincube|adinformation|adkmob|admax\.|"
    r"admixer|admob|admost|ads\.mdotm\.|adsafeprotected|adservice|"
    r"adsmogo|adsrvr|adswizz|adtag|adtech\.de|advert|adwhirl|"
    r"adz\.wattpad\.|alimama\.|alta\.eqmob\.|amazon-.*ads|"
    r"amazon\..*ads|amobee|analytics|anvato|appboy|appbrain|applovin|"
    r"applvn|appmetrica|appnext|appodeal|appsdt|appsflyer|apsalar|"
    r"avocarrot|axonix|banners-slb\.mobile\.yandex\.net|"
    r"banners\.mobile\.yandex\.net|brightcove\.|burstly|cauly|"
    r"cloudfront|cmcm\.|com\.google\.android\.gms\.ads\.identifier\."
    r"service\.START|comscore|contextual\.media\.net|crashlytics|"
    r"crispwireless|criteo\.|dmtry\.|doubleclick|duapps|dummy|flurry|"
    r"fwmrm|gad|getads|gimbal|glispa|google\.com\/dfp|googleAds|"
    r"googleads|googleapis\..*\.ad-.*|googlesyndication|"
    r"googletagmanager|greystripe|gstatic|heyzap|hyprmx|iasds01|"
    r"inmobi|inneractive|instreamatic|integralads|jumptag|jwpcdn|"
    r"jwpltx|jwpsrv|kochava|localytics|madnet|mapbox|mc\.yandex\.ru|"
    r"media\.net|metrics\.|millennialmedia|mixpanel|mng-ads\.com|"
    r"moat\.|moatads|mobclix|mobfox|mobpowertech|moodpresence|mopub|"
    r"native_ads|nativex\.|nexage\.|ooyala|openx\.|pagead|pingstart|"
    r"prebid|presage\.io|pubmatic|pubnative|rayjump|saspreview|"
    r"scorecardresearch|smaato|smartadserver|sponsorpay|"
    r"startappservice|startup\.mobile\.yandex\.net|"
    r"statistics\.videofarm\.daum\.net|supersonicads|taboola|tapas|"
    r"tapjoy|tapylitics|target\.my\.com|teads\.|umeng|unityads|"
    r'vungle|zucks).*"',
    r'"127.0.0.1"',
    "Ads Regex 10",
  ),
  (
    r"(invoke-interface \{[^\}]*\}, Lcom/google/android/vending/"
    r"licensing/Policy;->allowAccess\(\)Z[^>]*?\s+)move-result "
    r"([pv]\d+)",
    r"\1const/4 \2, 0x1",
    "Bypass Client-Side LVL (allowAccess)",
  ),
  (
    r"(\.method [^(]*connectToLicensingService\(\)V\s+"
    r".locals \d+)[\s\S]*?(\s+return-void\n.end method)",
    r"\1\2",
    "connectToLicensingService",
  ),
  (
    r"(\.method [^(]*initializeLicenseCheck\(\)V\s+"
    r".locals \d+)[\s\S]*?(\s+return-void\n.end method)",
    r"\1\2",
    "initializeLicenseCheck",
  ),
  (
    r"(\.method [^(]*processResponse\(ILandroid/os/Bundle;\)V\s+"
    r".locals \d+)[\s\S]*?(\s+return-void\n.end method)",
    r"\1\2",
    "processResponse",
  ),
]

# ⚡ Compile patterns once at module load
AD_PATTERNS: list[AdPattern] = [
  (re.compile(pattern, re.MULTILINE), replacement, description)
  for pattern, replacement, description in _RAW_PATTERNS
]
