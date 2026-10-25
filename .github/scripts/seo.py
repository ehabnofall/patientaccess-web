"""Static pages for search engines, written into the built site.

The app itself is Flutter (drawn on a canvas, with #/ routes), so Google sees
little of it. This script adds plain HTML pages that Google can read:
  /patients/ /doctors/ /pharmacies/ /labs/      what the site does for each
  /services/                                     the published ads, by kind
  /services/<ad id>/                             one page per published ad
plus robots.txt and sitemap.xml. Every page links into the app.

Run after `flutter build web`:  python3 tool/seo.py build/web
Ads named "(تجريبي)" (test data) are skipped.
"""
import html
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

SITE = 'https://patientaccess.site'
API = 'https://zimbemqqtvkewhbhjzat.supabase.co'
KEY = os.environ.get('SUPABASE_PUBLISHABLE_KEY') or \
    json.load(open(Path(__file__).parent.parent / 'config' / 'supabase.json'))['SUPABASE_PUBLISHABLE_KEY']
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else 'build/web')
TODAY = date.today().isoformat()

KINDS = {
    'clinic': ('العيادات', 'عيادة', 'MedicalClinic'),
    'hospital': ('المستشفيات', 'مستشفى', 'Hospital'),
    'pharmacy': ('الصيدليات', 'صيدلية', 'Pharmacy'),
    'lab': ('معامل التحاليل', 'معمل تحاليل', 'DiagnosticLab'),
    'radiology': ('مراكز الأشعة', 'مركز أشعة', 'DiagnosticLab'),
}
WD = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
WD_EN = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

e = html.escape

CSS = """
@font-face{font-family:Cairo;src:url('/assets/assets/fonts/Cairo-Regular.ttf');font-weight:400}
@font-face{font-family:Cairo;src:url('/assets/assets/fonts/Cairo-Bold.ttf');font-weight:700 900}
:root{--blue:#0A36B0;--navy:#062578;--green:#0B8A6E;--mint:#05C595;--tint:#E8F0FB;--line:#D9E3F0;--text:#13203A;--muted:#5B6B85}
*{box-sizing:border-box}body{margin:0;font-family:Cairo,Tahoma,sans-serif;color:var(--text);background:#F3F7FC;line-height:1.8}
header{background:#fff;border-bottom:1px solid var(--line)}
.wrap{max-width:960px;margin:0 auto;padding:0 18px}
header .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px;height:68px}
header img{height:44px}
nav a{color:var(--blue);text-decoration:none;font-weight:700;margin-inline-start:14px;font-size:15px}
.hero{background:linear-gradient(135deg,#E8F0FB,#DDF7EE);padding:38px 0 30px}
h1{color:var(--navy);font-size:32px;line-height:1.35;margin:0 0 8px}
h2{color:var(--blue);font-size:22px;margin:28px 0 8px}
.lead{font-size:18px;color:#24324D;margin:0 0 18px}
.btn{display:inline-block;background:linear-gradient(90deg,var(--blue),var(--navy));color:#fff;padding:10px 22px;border-radius:14px;text-decoration:none;font-weight:800;margin:4px 0 4px 8px}
.btn.alt{background:linear-gradient(90deg,var(--green),var(--mint))}
ul.feat{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
ul.feat li{background:#fff;border:1px solid var(--line);border-radius:16px;padding:14px 16px}
ul.feat b{display:block;color:var(--navy)}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin:10px 0}
.card a{color:var(--navy);font-weight:800;text-decoration:none;font-size:17px}
.muted{color:var(--muted);font-size:14px}
table{border-collapse:collapse;width:100%;background:#fff;border-radius:12px;overflow:hidden}
td{padding:6px 10px;border-top:1px solid var(--line)}
.tags span{display:inline-block;background:var(--tint);color:var(--navy);border-radius:20px;padding:2px 10px;margin:3px;font-size:14px}
footer{margin-top:40px;padding:22px 0;border-top:1px solid var(--line);color:var(--muted);font-size:14px}
footer a{color:var(--blue)}
"""

ROLES = {
    'patients': {
        'title': 'ملفك الطبي ومواعيدك وروشتتك في مكان واحد',
        'meta': 'بوابة المريض: ملف طبي واحد لك ولأطفالك، حجز مواعيد الأطباء أونلاين، روشتة إلكترونية على الموبايل، ونتائج التحاليل والأشعة في ملفك.',
        'lead': 'ملف طبي واحد لك ولأطفالك. لا يفتحه أي طبيب إلا بإذنك، وكل روشتة ونتيجة تُحفظ فيه.',
        'cta': ('/#/signup', 'أنشئ حسابك مجانًا'),
        'items': [
            ('ملف طبي واحد', 'التاريخ المرضي والحساسية والأمراض المزمنة والأدوية في مكان واحد، وملفات أطفالك تحت ١٨ سنة.'),
            ('أنت صاحب الإذن', 'تعطي العيادة كود أو QR لفتح ملفك، وتسحب الإذن متى شئت، وتعرف من فتح الملف.'),
            ('روشتة إلكترونية', 'تظهر على موبايلك، وتُصرف من الصيدلية مرة واحدة، ويمكنك إرسال رابطها لصيدليتك للتوصيل.'),
            ('حجز المواعيد أونلاين', 'ابحث عن طبيبك واختر وقتًا متاحًا، وانضم لقائمة الانتظار لو لم تجد موعدًا.'),
            ('تذكير قبل الموعد', 'رسالة على الإيميل وإشعار على الموبايل قبل الموعد بيوم.'),
            ('نتائج التحاليل والأشعة', 'يرفعها المعمل أو مركز الأشعة في ملفك مباشرة.'),
            ('كارت المريض', 'كارت مطبوع بـQR ثابت للعيادات والصيدليات، محمي بتاريخ ميلادك.'),
        ],
    },
    'doctors': {
        'title': 'نظام العيادة: ملف المريض، الروشتة الإلكترونية، وجدول المواعيد',
        'meta': 'بوابة المريض للأطباء والعيادات والمستشفيات: فتح ملف المريض بإذنه، روشتة إلكترونية من دليل الأدوية المصرية، طلب تحاليل وأشعة، وجدول مواعيد وحجز أونلاين.',
        'lead': 'افتح ملف المريض بإذنه بكود أو QR، واكتب الزيارة والروشتة وطلبات التحاليل، ودع الاستقبال يدير الجدول.',
        'cta': ('/#/signup', 'سجّل عيادتك'),
        'items': [
            ('ملف المريض كاملًا', 'الزيارات السابقة والحساسية والأدوية ونتائج التحاليل عند كل الأطباء الذين زارهم.'),
            ('روشتة إلكترونية', 'بحث في دليل الأدوية المصرية بالتركيزات والجرعات، وتنبيه للحساسية والتداخلات الدوائية.'),
            ('حماية من سوء الاستخدام', 'حد أقصى ٣٠ يومًا، ومنع تكرار الدواء قبل انتهائه إلا بسبب، ومتابعة أدوية الجداول.'),
            ('طلب تحاليل وأشعة', 'بـQR يفتحه المعمل، والنتيجة ترجع لملف المريض.'),
            ('جدول المواعيد', 'مواعيد العمل وأيام الإغلاق والحجوزات والحضور، للطبيب والاستقبال.'),
            ('حجز أونلاين وتذكير', 'المرضى يحجزون من الموقع، ويصلهم تذكير قبل الموعد بيوم.'),
            ('فريق العيادة', 'أطباء وتمريض واستقبال بصلاحيات مختلفة، والمدير يضيف ويحذف.'),
        ],
    },
    'pharmacies': {
        'title': 'صرف الروشتة الإلكترونية في صيدليتك',
        'meta': 'بوابة المريض للصيدليات: صرف الروشتة الإلكترونية بمسح QR مرة واحدة، كارت المريض، وروابط الروشتة التي يرسلها المريض على واتساب للتوصيل.',
        'lead': 'امسح رمز الروشتة واصرفها مرة واحدة، أو افتح الرابط الذي يرسله المريض على واتساب لتجهيز طلبه.',
        'cta': ('/#/signup', 'سجّل صيدليتك مجانًا'),
        'items': [
            ('صرف بمسح QR', 'الروشتة تُصرف مرة واحدة، والمريض يتبلّغ.'),
            ('كارت المريض', 'آخر الروشتات المفتوحة للمريض بعد التأكد من تاريخ ميلاده.'),
            ('التوصيل بالواتساب', 'المريض يرسل لك رابط روشتته الصالح ٢٤ ساعة، فتجهّز أدويته.'),
            ('صيدليات غير مشتركة', 'يمكن لأي صيدلية فتح الروشتة من رابطها وتسجيل الصرف، ما عدا أدوية الجداول.'),
            ('سجل الصرف', 'كل ما صرفته في مكان واحد.'),
        ],
    },
    'labs': {
        'title': 'معامل التحاليل ومراكز الأشعة: النتيجة في ملف المريض مباشرة',
        'meta': 'بوابة المريض للمعامل ومراكز الأشعة: فتح طلب الطبيب بـQR، ورفع نتيجة التحاليل أو تقرير الأشعة PDF إلى ملف المريض مجانًا.',
        'lead': 'افتح طلب الطبيب بـQR، وارفع النتيجة PDF إلى ملف المريض، فيصل للطبيب والمريض فورًا.',
        'cta': ('/#/signup', 'سجّل معملك أو مركزك مجانًا'),
        'items': [
            ('طلب الطبيب بـQR', 'التحاليل أو الأشعة المطلوبة وملاحظات الطبيب.'),
            ('رفع النتيجة', 'PDF أو صورة إلى ملف المريض، ويصله إيميل.'),
            ('كارت المريض', 'لو جاء المريض من غير طلب.'),
            ('سجل المرضى والنتائج', 'كل ما رفعته في مكان واحد.'),
        ],
    },
}
ROLE_NAV = [('patients', 'للمرضى'), ('doctors', 'للأطباء'), ('pharmacies', 'للصيدليات'), ('labs', 'للمعامل والأشعة'), ('services', 'دليل المنشآت')]


def page(path, title, meta, body, jsonld=None):
    nav = ''.join(f'<a href="/{k}/">{e(n)}</a>' for k, n in ROLE_NAV)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ''
    doc = f'''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | بوابة المريض</title>
<meta name="description" content="{e(meta)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website"><meta property="og:site_name" content="بوابة المريض | Patient Access">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(meta)}">
<meta property="og:url" content="{SITE}{path}"><meta property="og:image" content="{SITE}/og.jpg"><meta property="og:locale" content="ar_EG">
<link rel="icon" href="/favicon.png"><style>{CSS}</style>{ld}</head><body>
<header><div class="wrap"><a href="/"><img src="/assets/assets/images/logo_wide.png" alt="بوابة المريض Patient Access"></a><nav>{nav}</nav></div></header>
{body}
<footer><div class="wrap">بوابة المريض · Patient Access · <a href="/">patientaccess.site</a> · <a href="/#/terms">الشروط</a> · <a href="/#/privacy">الخصوصية</a></div></footer>
</body></html>'''
    f = OUT / path.strip('/') / 'index.html'
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(doc, encoding='utf-8')


def role_pages():
    for key, r in ROLES.items():
        items = ''.join(f'<li><b>{e(t)}</b>{e(d)}</li>' for t, d in r['items'])
        body = f'''<section class="hero"><div class="wrap"><h1>{e(r['title'])}</h1><p class="lead">{e(r['lead'])}</p>
<a class="btn" href="{r['cta'][0]}">{e(r['cta'][1])}</a><a class="btn alt" href="/#/login">تسجيل الدخول</a></div></section>
<main class="wrap"><h2>ماذا تقدم بوابة المريض</h2><ul class="feat">{items}</ul></main>'''
        page(f'/{key}/', r['title'], r['meta'], body)


def api(fn, params):
    req = urllib.request.Request(f'{API}/rest/v1/rpc/{fn}', data=json.dumps(params).encode(),
                                 headers={'apikey': KEY, 'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def hours_text(h):
    if h == '24h':
        return [('كل الأيام', '24 ساعة')]
    out = []
    for w in [6, 0, 1, 2, 3, 4, 5]:
        v = (h or {}).get(str(w))
        out.append((WD[w], 'مغلق' if not isinstance(v, list) else '  ·  '.join(f'{p[0]}–{p[1]}' for p in v)))
    return out


def opening_spec(h):
    if h == '24h':
        return [{'@type': 'OpeningHoursSpecification', 'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                 'opens': '00:00', 'closes': '23:59'}]
    names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    out = []
    for w in range(7):
        v = (h or {}).get(str(w))
        if isinstance(v, list):
            for p in v:
                out.append({'@type': 'OpeningHoursSpecification', 'dayOfWeek': names[w], 'opens': p[0], 'closes': p[1]})
    return out


def services_pages():
    urls = []
    all_ads = []
    for kind in KINDS:
        page_no = 0
        while True:
            rows = api('search_ads', {'p_kind': kind, 'p_page': page_no})
            for r in rows:
                a = r['ad']
                if 'تجريبي' in a['name'] and not os.environ.get('SEO_INCLUDE_TEST'):
                    continue
                a['rating'], a['reviews'] = r.get('rating'), r.get('reviews')
                all_ads.append(a)
            if len(rows) < 20:
                break
            page_no += 1
    by_kind = {k: [a for a in all_ads if a['kind'] == k] for k in KINDS}
    for a in all_ads:
        plural, single, schema = KINDS[a['kind']]
        d = a.get('details') or {}
        tags = ''.join(f'<span>{e(t)}</span>' for t in a.get('tags') or [])
        hours = ''.join(f'<tr><td>{e(x)}</td><td dir="ltr" style="text-align:right">{e(y)}</td></tr>' for x, y in hours_text(a['hours']))
        phones = ' · '.join(f'<a href="tel:{e(p)}">{e(p)}</a>' for p in a['phones'])
        docs = ''.join(f'<li>{e(x["name"])}{" – " + e(x.get("title") or "") if x.get("title") else ""}{" – " + e(x.get("specialty") or "") if x.get("specialty") else ""}</li>'
                       for x in d.get('doctors') or [])
        place = ' · '.join(x for x in [a['governorate'], a.get('city')] if x)
        title = f"{a['name']} – {single} في {place}"
        meta = f"{a['name']}، {single} في {place}. العنوان: {a['address']}. {' ، '.join((a.get('tags') or [])[:5])}"[:300]
        photo = f"{API}/storage/v1/object/public/ads/{a['photos'][0]}" if a.get('photos') else None
        body = f'''<section class="hero"><div class="wrap"><h1>{e(a['name'])}</h1>
<p class="lead">{e(single)} · {e(place)}</p>
{f'<img src="{e(photo)}" alt="{e(a["name"])}" style="max-width:100%;border-radius:16px">' if photo else ''}
<p><a class="btn" href="/#/ads/{a['id']}">التفاصيل والتواصل</a></p></div></section>
<main class="wrap">
{f'<p>{e(a["description"])}</p>' if a.get('description') else ''}
<h2>العنوان والتواصل</h2><p>{e(a['address'])}<br>{phones}</p>
{f'<h2>التخصصات والخدمات</h2><p class="tags">{tags}</p>' if tags else ''}
{f'<h2>الأطباء</h2><ul>{docs}</ul>' if docs else ''}
<h2>مواعيد العمل</h2><table>{hours}</table>
<p class="muted"><a href="/services/">كل المنشآت</a></p></main>'''
        ld = {'@context': 'https://schema.org', '@type': schema, 'name': a['name'], 'url': f"{SITE}/services/{a['id']}/",
              'telephone': a['phones'][0], 'address': {'@type': 'PostalAddress', 'streetAddress': a['address'],
              'addressLocality': a.get('city') or a['governorate'], 'addressRegion': a['governorate'], 'addressCountry': 'EG'},
              'openingHoursSpecification': opening_spec(a['hours'])}
        if photo:
            ld['image'] = photo
        if a.get('lat') is not None:
            ld['geo'] = {'@type': 'GeoCoordinates', 'latitude': a['lat'], 'longitude': a['lng']}
        if a.get('rating') and a.get('reviews'):
            ld['aggregateRating'] = {'@type': 'AggregateRating', 'ratingValue': a['rating'], 'reviewCount': a['reviews']}
        page(f"/services/{a['id']}/", title, meta, body, ld)
        urls.append(f"/services/{a['id']}/")
    sections = ''
    for kind, (plural, single, _) in KINDS.items():
        lst = by_kind[kind]
        cards = ''.join(f'''<div class="card"><a href="/services/{a['id']}/">{e(a['name'])}</a>
<div class="muted">{e(a['governorate'])}{' · ' + e(a['city']) if a.get('city') else ''} · {e(a['address'])}</div></div>''' for a in lst)
        sections += f'<h2>{e(plural)}</h2>' + (cards or '<p class="muted">لا توجد منشآت منشورة بعد.</p>')
    body = f'''<section class="hero"><div class="wrap"><h1>دليل المنشآت الطبية الموثّقة</h1>
<p class="lead">عيادات ومستشفيات وصيدليات ومعامل تحاليل ومراكز أشعة موثّقة على بوابة المريض.</p>
<a class="btn" href="/#/ads">ابحث بالمحافظة والتخصص</a></div></section><main class="wrap">{sections}</main>'''
    page('/services/', 'دليل المنشآت الطبية الموثّقة', 'دليل العيادات والمستشفيات والصيدليات ومعامل التحاليل ومراكز الأشعة الموثّقة في مصر على بوابة المريض، مع العناوين ومواعيد العمل وأرقام التليفون.', body)
    return urls


def main():
    import shutil
    shutil.rmtree(OUT / 'services', ignore_errors=True)
    role_pages()
    ad_urls = services_pages()
    urls = ['/', '/patients/', '/doctors/', '/pharmacies/', '/labs/', '/services/'] + ad_urls
    sm = ''.join(f'<url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>' for u in urls)
    (OUT / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>', encoding='utf-8')
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')
    print(len(urls), 'urls;', len(ad_urls), 'ads')


main()
