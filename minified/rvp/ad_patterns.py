from __future__ import annotations

_A = "\\1\\2"
import re
from re import Pattern

AdPattern = tuple[Pattern[str], str, str]
_RAW_PATTERNS = [
  (
    '"(com.google.android.play.core.appupdate.protocol.IAppUpdateService|Theme.Dialog.Alert|com.google.android.play.core.install.BIND_UPDATE_SERVICE)"',
    '""',
    "Update Disable",
  ),
  (
    "(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->(.*load|show.*)\\([^)]*\\)V)|(invoke(?!.*(close|Deactiv|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop|Throw)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->(request.*|(.*(activat|Banner|build|Event|exec|header|html|initAd|initi|JavaScript|Interstitial|load|log|MetaData|metri|Native|onAd|propert|report|response|Rewarded|show|trac|url|(fetch|refresh|render|video)Ad).*)|.*Request)\\([^)]*\\)V)|(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->((.*(Banner|initAd|Interstitial|load|Native|onAd|Rewarded|show|(fetch|refresh|render|request|video)Ad).*))\\([^)]*\\)V)|invoke-.*\\{.*\\}, L[^;]+;->(loadAd|requestNativeAd|showInterstitial|fetchad|fetchads|onadloaded|requestInterstitialAd|showAd|loadAds|AdRequest|requestBannerAd|loadNextAd|createInterstitialAd|setNativeAd|loadBannerAd|loadNativeAd|loadRewardedAd|loadRewardedInterstitialAd|loadAds|loadAdViewAd|showInterstitialAd|shownativead|showbannerad|showvideoad|onAdFailedToLoad)\\([^)]*\\)V|invoke-[^{]+ \\{[^\\}]*\\}, Lcom[^;]+;->requestInterstitialAd\\([^)]*\\)V|invoke-[^{]+ \\{[^\\}]*\\}, Lcom[^;]+;->loadAds\\([^)]*\\)V|invoke-[^{]+ \\{[^\\}]*\\}, Lcom[^;]+;->loadAd\\([^)]*\\)V|invoke-[^{]+ \\{[^\\}]*\\}, Lcom[^;]+;->requestBannerAd\\([^)]*\\)V|invoke-[^{]+ \\{[pv]\\d\\}, Lcom/facebook[^;]+;->show\\([^)]*\\)V|invoke-[^{]+ \\{[pv]\\d\\}, Lcom/google[^;]+;->show\\([^)]*\\)V",
    "nop",
    "Ads Regex 1",
  ),
  (
    "(invoke(?!.*(close|Deactiv|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop|Throw)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->(request.*|(.*(activat|Banner|build|Event|exec|header|html|initAd|initi|JavaScript|Interstitial|load|log|MetaData|metri|Native|(can|get|is|has|was)Ad|propert|report|response|Rewarded|show|trac|url|(fetch|refresh|render|video)Ad).*)|.*Request)\\([^)]*\\)Z[^>]*?)move-result ([pv]\\d+)|(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->((.*(Banner|initAd|Interstitial|load|Native|(can|get|has|is|was)Ad|Rewarded|show|(fetch|refresh|render|request|video)Ad).*))\\([^)]*\\)Z[^>]*?)move-result ([pv]\\d+)",
    "const/4 \\9, 0x0",
    "Ads Regex 2",
  ),
  (
    "(invoke(?!.*(close|Destroy|Dismiss|Disabl|error|player|remov|expir|fail|hide|skip|stop)).*/(adcolony|admob|ads|adsdk|aerserv|appbrain|applovin|appodeal|appodealx|appsflyer|bytedance/sdk/openadsdk|chartboost|flurry|fyber|hyprmx|inmobi|ironsource|mbrg|mbridge|mintegral|moat|mobfox|mobilefuse|mopub|my/target|ogury|Omid|onesignal|presage|smaato|smartadserver|snap/adkit|snap/appadskit|startapp|taboola|tapjoy|tappx|vungle)/[^;]+;->(.*(load|show).*)\\([^)]*\\)Z[^>]*?)move-result ([pv]\\d+)",
    "const/4 \\6, 0x0",
    "Ads Regex 3",
  ),
  (
    "(\\.method\\s(public|private|static)\\s\\b(?!\\babstract|native\\b)[^(]*?loadAd\\([^)]*\\)V)",
    "\\1\\n\\treturn-void",
    "Ads Regex 4",
  ),
  (
    "(\\.method\\s(public|private|static)\\s\\b(?!\\babstract|native\\b)[^(]*?loadAd\\([^)]*\\)Z)",
    "\\1\\n\\tconst/4 v0, 0x0\\n\\treturn v0",
    "Ads Regex 5",
  ),
  (
    "(invoke[^{]+ \\{[^\\}]*\\}, L[^(]*loadAd\\([^)]*\\)[VZ])|(invoke[^{]+ \\{[^\\}]*\\}, L[^(]*gms.*\\>(loadUrl|loadDataWithBaseURL|requestInterstitialAd|showInterstitial|showVideo|showAd|loadData|onAdClicked|onAdLoaded|isLoading|loadAds|AdLoader|AdRequest|AdListener|AdView)\\([^)]*\\)V)",
    "#",
    "Ads Regex 6",
  ),
  (
    "\\.method [^(]*(loadAd|requestNativeAd|showInterstitial|fetchad|fetchads|onadloaded|requestInterstitialAd|showAd|loadAds|AdRequest|requestBannerAd|loadNextAd|createInterstitialAd|setNativeAd|loadBannerAd|loadNativeAd|loadRewardedAd|loadRewardedInterstitialAd|loadAds|loadAdViewAd|showInterstitialAd|shownativead|showbannerad|showvideoad|onAdFailedToLoad)\\([^)]*\\)V\\s+\\.locals \\d+[\\s\\S]*?\\.end method",
    "#",
    "Ads Regex 7",
  ),
  (
    '"ca-app-pub-\\d{16}/\\d{10}"',
    '"ca-app-pub-0000000000000000/0000000000"',
    "Ads Regex 8",
  ),
  (
    '"(http.*|//.*)(61.145.124.238|-ads.|.ad.|.ads.|.analytics.localytics.com|.mobfox.com|.mp.mydas.mobi|.plus1.wapstart.ru|.scorecardresearch.com|.startappservice.com|/ad.|/ads|ad-mail|ad.*_logging|ad.api.kaffnet.com|adc3-launch|adcolony|adinformation|adkmob|admax|admob|admost|adsafeprotected|adservice|adtag|advert|adwhirl|adz.wattpad.com|alta.eqmob.com|amazon-*ads|amazon.*ads|amobee|analytics|applovin|applvn|appnext|appodeal|appsdt|appsflyer|burstly|cauly|cloudfront|com.google.android.gms.ads.identifier.service.START|crashlytics|crispwireless|doubleclick|dsp.batmobil.net|duapps|dummy|flurry|gad|getads|google.com/dfp|googleAds|googleads|googleapis.*.ad-*|googlesyndication|googletagmanager|greystripe|gstatic|inmobi|inneractive|jumptag|live.chartboost.com|madnet|millennialmedia|moatads|mopub|native_ads|pagead|pubnative|smaato|supersonicads|tapas|tapjoy|unityads|vungle|zucks).*"',
    '"="',
    "Ads Regex 9",
  ),
  (
    '"(http.*|//.*)(61\\.145\\.124\\.238|/2mdn\\.net|-ads\\.|\\.5rocks\\.io|\\.ad\\.|\\.adadapted|\\.admitad\\.|\\.admost\\.|\\.ads\\.|\\.aerserv\\.|\\.airpush\\.|\\.batmobil\\.|\\.chartboost\\.|\\.cloudmobi\\.|\\.conviva\\.|\\.dov-e\\.com|\\.fyber\\.|\\.mng-ads\\|\\.mydas\\.|\\.predic\\.|\\.talkingdata\\.|\\.tapdaq\\.|\\.tele\\.fm|\\.unity3d\\.|\\.unity\\.|\\.wapstart\\.|\\.xdrig\\.|\\.zapr\\.|\\/ad\\.|/ads|a4\\.tl|accengage|ad4push|ad4screen|ad-mail|ad\\..*_logging|ad\\.api\\.kaffnet\\.|ad\\.cauly\\.co\\.|adbuddiz|adc3-launch|adcolony|adfurikun|adincube|adinformation|adkmob|admax\\.|admixer|admob|admost|ads\\.mdotm\\.|adsafeprotected|adservice|adsmogo|adsrvr|adswizz|adtag|adtech\\.de|advert|adwhirl|adz\\.wattpad\\.|alimama\\.|alta\\.eqmob\\.|amazon-.*ads|amazon\\..*ads|amobee|analytics|anvato|appboy|appbrain|applovin|applvn|appmetrica|appnext|appodeal|appsdt|appsflyer|apsalar|avocarrot|axonix|banners-slb\\.mobile\\.yandex\\.net|banners\\.mobile\\.yandex\\.net|brightcove\\.|burstly|cauly|cloudfront|cmcm\\.|com\\.google\\.android\\.gms\\.ads\\.identifier\\.service\\.START|comscore|contextual\\.media\\.net|crashlytics|crispwireless|criteo\\.|dmtry\\.|doubleclick|duapps|dummy|flurry|fwmrm|gad|getads|gimbal|glispa|google\\.com\\/dfp|googleAds|googleads|googleapis\\..*\\.ad-.*|googlesyndication|googletagmanager|greystripe|gstatic|heyzap|hyprmx|iasds01|inmobi|inneractive|instreamatic|integralads|jumptag|jwpcdn|jwpltx|jwpsrv|kochava|localytics|madnet|mapbox|mc\\.yandex\\.ru|media\\.net|metrics\\.|millennialmedia|mixpanel|mng-ads\\.com|moat\\.|moatads|mobclix|mobfox|mobpowertech|moodpresence|mopub|native_ads|nativex\\.|nexage\\.|ooyala|openx\\.|pagead|pingstart|prebid|presage\\.io|pubmatic|pubnative|rayjump|saspreview|scorecardresearch|smaato|smartadserver|sponsorpay|startappservice|startup\\.mobile\\.yandex\\.net|statistics\\.videofarm\\.daum\\.net|supersonicads|taboola|tapas|tapjoy|tapylitics|target\\.my\\.com|teads\\.|umeng|unityads|vungle|zucks).*"',
    '"127.0.0.1"',
    "Ads Regex 10",
  ),
  (
    "(invoke-interface \\{[^\\}]*\\}, Lcom/google/android/vending/licensing/Policy;->allowAccess\\(\\)Z[^>]*?\\s+)move-result ([pv]\\d+)",
    "\\1const/4 \\2, 0x1",
    "Bypass Client-Side LVL (allowAccess)",
  ),
  (
    "(\\.method [^(]*connectToLicensingService\\(\\)V\\s+.locals \\d+)[\\s\\S]*?(\\s+return-void\\n.end method)",
    _A,
    "connectToLicensingService",
  ),
  (
    "(\\.method [^(]*initializeLicenseCheck\\(\\)V\\s+.locals \\d+)[\\s\\S]*?(\\s+return-void\\n.end method)",
    _A,
    "initializeLicenseCheck",
  ),
  (
    "(\\.method [^(]*processResponse\\(ILandroid/os/Bundle;\\)V\\s+.locals \\d+)[\\s\\S]*?(\\s+return-void\\n.end method)",
    _A,
    "processResponse",
  ),
]
AD_PATTERNS = [(re.compile(A, re.MULTILINE), B, C) for (A, B, C) in _RAW_PATTERNS]
