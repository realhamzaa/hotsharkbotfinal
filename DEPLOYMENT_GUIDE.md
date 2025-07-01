# دليل نشر بوت HOT SHARK 🐋

## نظرة عامة
بوت HOT SHARK هو بوت تيليجرام متقدم لتداول الفوركس والذهب والعملات الرقمية مع ميزات الذكاء الاصطناعي وتحليل ICT/SMC.

## الميزات الرئيسية
- 🤖 **تحليل تلقائي 24/7** مع الذكاء الاصطناعي
- 📊 **تحليل ICT/SMC** متقدم
- 🔄 **نظام جلسة واحدة** لكل مستخدم
- 📅 **كتالوج السوق** مع مواعيد الأسواق والسيولة
- 🌍 **دعم متعدد اللغات** (العربية والإنجليزية)
- 📈 **توصيات تلقائية** مع نسب نجاح محسوبة
- 🔔 **مراقبة السوق المستمرة** مع التنبيهات
- 📱 **لوحة إدارة ويب** شاملة

## المتطلبات الأساسية

### 1. إنشاء بوت تيليجرام
1. تحدث مع [@BotFather](https://t.me/BotFather) على تيليجرام
2. أرسل `/newbot` واتبع التعليمات
3. احفظ رمز البوت (Bot Token)
4. فعّل وضع الـ Inline للبوت (اختياري)

### 2. الحصول على معرف المسؤول
1. أرسل رسالة لبوت [@userinfobot](https://t.me/userinfobot)
2. احفظ معرف المستخدم (User ID)

## إعداد البيئة المحلية

### 1. تثبيت ال### 1. تثبيت المتطلبات
```bash
# تأكد من وجود Python 3.11+
python3 --version

# انتقل لمجلد المشروع
cd hot_shark_bot

# تثبيت المتطلبات
pip3 install -r requirements.txt
```

### 2. إعداد متغيرات البيئة
انسخ ملف `.env.example` إلى `.env` وعدّل القيم:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-app-name.onrender.com
ADMIN_USER_ID=your_telegram_user_id

# Database Configuration
DATABASE_URL=sqlite:///./hot_shark_bot.db

# Security
SECRET_KEY=your_secret_key_here

# Environment
ENVIRONMENT=production

# API Keys (Optional)
TWELVE_DATA_API_KEY=your_twelve_data_api_key
POLYGON_API_KEY=your_polygon_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key

# Server Configuration
PORT=8000
```

### 3. اختبار البوت محلياً
```bash
# تشغيل الاختبارات
python3 test_bot.py

# تشغيل الخادم للاختبار المحلي
python3 main.py
```

## النشر على Render (مجاني) - باستخدام Docker

### 1. إعداد المستودع
1. ارفع المشروع على GitHub
2. تأكد من وجود الملفات التالية:
   - `Dockerfile` (ملف Docker الجديد)
   - `.dockerignore` (لتحسين عملية البناء)
   - `requirements.txt`
   - `main.py`
   - `render.yaml` (محدث ليستخدم Docker)

### 2. إنشاء خدمة على Render

#### خطوة 1: إنشاء حساب
- اذهب إلى [render.com](https://render.com)
- أنشئ حساب جديد أو سجل دخول

#### خطوة 2: ربط GitHub
- اربط حساب GitHub مع Render
- امنح الصلاحيات اللازمة

#### خطوة 3: إنشاء Web Service
1. اضغط "New +" ثم "Web Service"
2. اختر المستودع من GitHub
3. املأ الإعدادات:
   - **Name:** `hot-shark-bot`
   - **Environment:** `Docker` (مهم جداً!)
   - **Region:** اختر الأقرب لك
   - **Branch:** `main`
   - **Dockerfile Path:** `./Dockerfile` (سيتم اكتشافه تلقائياً)

**ملاحظة مهمة:** تأكد من اختيار `Docker` كبيئة التشغيل، وليس `Python`. هذا سيحل مشكلة عدم توافق `pandas` مع Python 3.13.

#### خطوة 4: إعداد متغيرات البيئة
أضف المتغيرات التالية في قسم "Environment Variables":

```
TELEGRAM_BOT_TOKEN=your_actual_bot_token
TELEGRAM_WEBHOOK_URL=https://your-app-name.onrender.com
ADMIN_USER_ID=your_user_id
DATABASE_URL=sqlite:///./hot_shark_bot.db
SECRET_KEY=your_secret_key
ENVIRONMENT=production
PORT=10000
```

#### خطوة 5: النشر
1. اضغط "Create Web Service"
2. انتظر حتى اكتمال البناء والنشر (5-10 دقائق)
3. ستحصل على رابط مثل: `https://your-app-name.onrender.com`

### 3. إعداد Webhook
بعد النشر الناجح، قم بإعداد webhook:

```bash
# استبدل YOUR_BOT_TOKEN و YOUR_RENDER_URL
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://YOUR_RENDER_URL/webhook/YOUR_BOT_TOKEN"}'
```

أو استخدم المتصفح:
```
https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=https://YOUR_RENDER_URL/webhook/YOUR_BOT_TOKEN
```

### 4. التحقق من النشر
- تحقق من الحالة: `https://your-app-name.onrender.com/health`
- اختبر البوت بإرسال `/start` في تيليجرام
- تحقق من لوحة الإدارة: `https://your-app-name.onrender.com/admin/`

## استخدام البوت

### 1. أوامر المستخدمين
- `/start` - بدء استخدام البوت
- `📊 الكتالوج` - عرض مواعيد الأسواق والسيولة
- `📈 التوصيات` - عرض آخر التوصيات
- `📰 الأخبار` - عرض الأخبار المهمة
- `⚙️ الإعدادات` - إعدادات المستخدم
- `🌐 تغيير اللغة` - التبديل بين العربية والإنجليزية

### 2. أوامر الإدارة

#### إدارة المستخدمين:
```
/add_subscription [user_id] [days] - إضافة اشتراك
/remove_subscription [user_id] - إلغاء اشتراك
/list_users - عرض قائمة المستخدمين
```

#### إرسال التوصيات:
```
/send_rec XAUUSD BUY 1950,1948 1960,1965 1945 15 85 short 1:2 0.01 premium ICT_BOS live
```

#### إرسال الأخبار:
```
/send_news "عنوان الخبر" "2024-01-15 14:30" USD high "وصف الخبر" critical
```

#### تحديث الصفقات:
```
/update_trade [recommendation_id] [status]
```

### 3. لوحة الإدارة الويب
- **الرابط:** `https://your-app-name.onrender.com/admin/`
- **كلمة المرور الافتراضية:** `admin123`
- **الميزات:**
  - إدارة المستخدمين والاشتراكات
  - إرسال التوصيات والأخبار
  - عرض الإحصائيات والتقارير
  - إعدادات النظام
  - مراقبة الأداء

## الميزات المتقدمة

### 1. نظام الجلسة الواحدة
- كل مستخدم يمكنه الحصول على جلسة واحدة فقط
- إنهاء الجلسات السابقة تلقائياً عند تسجيل دخول جديد
- حماية من الاستخدام المتعدد

### 2. كتالوج السوق
- مواعيد فتح وإغلاق الأسواق
- أوقات السيولة القوية
- معلومات أزواج العملات المدعومة
- تنبيهات السيولة التلقائية

### 3. مراقبة السوق 24/7
- تحليل مستمر للأسواق
- إرسال تنبيهات فورية
- كشف الفرص التجارية
- تحديث البيانات كل دقيقة

### 4. الذكاء الاصطناعي وتحليل ICT/SMC
- تحليل Order Blocks
- كشف Fair Value Gaps
- تحديد مناطق السيولة
- حساب نسب النجاح تلقائياً

## الصيانة والمراقبة

### 1. مراقبة الحالة
```bash
# التحقق من حالة البوت
curl https://your-app-name.onrender.com/health

# عرض إحصائيات البوت
curl https://your-app-name.onrender.com/status
```

### 2. السجلات
- عرض السجلات في لوحة تحكم Render
- مراقبة الأخطاء والتحذيرات
- تتبع أداء البوت

### 3. النسخ الاحتياطي
- قاعدة البيانات محفوظة تلقائياً
- تحميل نسخة احتياطية من لوحة الإدارة
- استعادة البيانات عند الحاجة

## الأمان والحماية

### 1. أمان البوت
- تشفير جميع البيانات الحساسة
- التحقق من صحة المدخلات
- حماية من الهجمات الشائعة

### 2. إدارة الوصول
- نظام صلاحيات متدرج
- حماية لوحة الإدارة بكلمة مرور
- تسجيل جميع العمليات

### 3. أفضل الممارسات
```bash
# غيّر كلمة مرور لوحة الإدارة فوراً
# لا تشارك رموز البوت مع أحد
# استخدم HTTPS دائماً
# راقب السجلات بانتظام
```

## استكشاف الأخطاء

### مشاكل شائعة:

#### 1. البوت لا يرد:
```bash
# تحقق من صحة Bot Token
curl "https://api.telegram.org/botYOUR_TOKEN/getMe"

# تحقق من Webhook
curl "https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo"
```

#### 2. خطأ في النشر:
- راجع سجلات البناء في Render
- تأكد من صحة `requirements.txt`
- تحقق من متغيرات البيئة

#### 3. مشاكل قاعدة البيانات:
- تحقق من مسار قاعدة البيانات
- راجع صلاحيات الكتابة
- استخدم SQLite للبساطة

### الحصول على المساعدة:
1. راجع السجلات في Render Dashboard
2. استخدم `/health` للتحقق من الحالة
3. اختبر البوت محلياً أولاً
4. تحقق من التوثيق في `/docs`

## تحديثات مستقبلية

### الميزات المخططة:
- 📊 تحليلات أكثر تقدماً
- 🔔 تنبيهات مخصصة
- 📱 تطبيق موبايل
- 🤖 ذكاء اصطناعي محسّن
- 📈 مؤشرات تقنية إضافية

### كيفية التحديث:
1. ادفع التحديثات إلى GitHub
2. Render سيعيد النشر تلقائياً
3. راقب عملية النشر
4. اختبر الميزات الجديدة

---

## ملاحظات مهمة

⚠️ **تحذيرات:**
- غيّر كلمة مرور لوحة الإدارة فوراً
- لا تشارك رموز البوت مع أحد
- استخدم HTTPS في الإنتاج
- راقب استخدام الموارد على Render

✅ **نصائح للنجاح:**
- اختبر البوت محلياً قبل النشر
- راقب الأداء والسجلات بانتظام
- احتفظ بنسخ احتياطية منتظمة
- تفاعل مع المستخدمين واستمع لملاحظاتهم

🎯 **الدعم الفني:**
- استخدم `test_bot.py` لتشخيص المشاكل
- راجع التوثيق في `/docs`
- تحقق من حالة النظام في `/health`
- استخدم لوحة الإدارة لمراقبة الأداء

🚀 **للمطورين:**
- الكود مفتوح المصدر ومنظم
- يمكن إضافة ميزات جديدة بسهولة
- يدعم التوسع والتطوير
- موثق بالكامل ومختبر

---

**بوت HOT SHARK جاهز للاستخدام! 🐋**


