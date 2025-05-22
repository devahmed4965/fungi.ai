// static/script.js
document.addEventListener('DOMContentLoaded', () => {

    // --- Confidence Bar Animation ---
    const animateConfidenceBars = () => {
        document.querySelectorAll('.confidence-fill').forEach(bar => {
            const targetWidth = bar.getAttribute('data-width').replace('%', '');
            if (targetWidth && !isNaN(targetWidth)) { // تأكد أنه رقم صالح
                requestAnimationFrame(() => {
                    // لا تحتاج لتأخير setTimeout هنا عادةً
                    bar.style.width = targetWidth + '%';
                });
            }
        });
    };
    animateConfidenceBars(); // تشغيل الأنيميشن عند تحميل الصفحة

    // --- File Input Handling ---
    const fileInput = document.getElementById('file-upload');
    const fileUploadText = document.getElementById('file-upload-text');
    // الحصول على النص الافتراضي من العنصر نفسه (أو يمكنك تحديده هنا إذا كان ثابتًا)
    const defaultUploadText = fileUploadText ? fileUploadText.textContent : "اختر صورة فطر للتحليل أو اسحبها هنا";

    if (fileInput && fileUploadText) {
         fileInput.addEventListener('change', function() {
             const fileName = this.files[0]?.name;
             if (fileName) {
                 // استخدام نص يتغير حسب اللغة (إذا كنت تستخدم i18n في JS)
                 // حاليًا نستخدم نصًا ثابتًا كمثال
                 fileUploadText.textContent = `الملف: ${fileName}`;
             } else {
                 fileUploadText.textContent = defaultUploadText;
             }
         });
    }

    // --- Loading Indicator ---
    const uploadForm = document.getElementById('upload-form');
    const loaderWrapper = document.getElementById('loader-wrapper');

    if (uploadForm && loaderWrapper && fileInput) { // تأكد من وجود fileInput
        uploadForm.addEventListener('submit', (event) => {
            // التحقق من وجود ملف قبل إظهار اللودر
            if (fileInput.files.length === 0) {
                // يمكنك عرض رسالة خطأ هنا أو منع الإرسال
                // event.preventDefault(); // لمنع الإرسال إذا لم يتم اختيار ملف
                // alert("Please select a file first.");
                return; // لا تظهر اللودر إذا لم يتم اختيار ملف
            }
            loaderWrapper.style.display = 'flex'; // إظهار اللودر
        });
    }

    // --- Language Switcher ---
    const langSwitchButton = document.querySelector('.lang-switch');
    if (langSwitchButton) {
        langSwitchButton.addEventListener('click', () => {
            const currentLang = document.documentElement.lang; // الحصول على اللغة الحالية من <html>
            const newLang = (currentLang === 'ar') ? 'en' : 'ar';
            // بناء الرابط الأساسي للصفحة الحالية (بدون query parameters)
            const baseUrl = window.location.origin + window.location.pathname;
            // الانتقال إلى الصفحة مع تحديد اللغة الجديدة كـ query parameter
            window.location.href = baseUrl + "?lang=" + newLang;
        });
    }

    // ملاحظة: إذا كنت ستستخدم AJAX لاحقًا لعرض النتائج دون إعادة تحميل الصفحة،
    // ستحتاج إلى استدعاء animateConfidenceBars() مرة أخرى بعد إضافة النتائج إلى DOM
    // وإخفاء loaderWrapper يدويًا عند اكتمال الطلب.

});
// static/script.js
document.addEventListener('DOMContentLoaded', () => {

    // --- Welcome Splash Hiding Logic ---
    const splashScreen = document.getElementById('welcome-splash');
    if (splashScreen) {
        // تحديد مدة ظهور الرسالة الترحيبية (بالمللي ثانية)
        const splashDuration = 2500; // 2.5 ثانية

        // إخفاء الرسالة بعد المدة المحددة
        setTimeout(() => {
            splashScreen.classList.add('hidden');

            // اختياري: إزالة العنصر بالكامل من DOM بعد انتهاء تأثير الاختفاء
            // هذا يحسن الأداء قليلًا لأنه يزيل عنصرًا غير ضروري
            setTimeout(() => {
                if (splashScreen.parentNode) {
                    splashScreen.parentNode.removeChild(splashScreen);
                }
            }, 800); // يجب أن تتطابق هذه المدة مع مدة الانتقال في CSS (0.8s)

        }, splashDuration);
    }
    // --- نهاية منطق إخفاء Welcome Splash ---


    // --- Confidence Bar Animation ---
    const animateConfidenceBars = () => {
        // ... (الكود كما هو) ...
    };
    // لا تستدعيها هنا مباشرة إذا كان هناك Splash Screen
    // يمكنك تأخيرها قليلًا أو استدعاؤها بعد إخفاء الـ splash
    // animateConfidenceBars();


    // --- File Input Handling ---
    const fileInput = document.getElementById('file-upload');
    const fileUploadText = document.getElementById('file-upload-text');
    const defaultUploadText = fileUploadText ? fileUploadText.textContent : "اختر صورة فطر للتحليل أو اسحبها هنا";
    // ... (الكود كما هو) ...


    // --- Loading Indicator ---
    const uploadForm = document.getElementById('upload-form');
    const loaderWrapper = document.getElementById('loader-wrapper');
    // ... (الكود كما هو) ...


    // --- Language Switcher ---
    const langSwitchButton = document.querySelector('.lang-switch');
    // ... (الكود كما هو) ...

    // يمكن تأخير استدعاء أنيميشن شريط الثقة هنا قليلًا
    // لضمان اختفاء شاشة الترحيب أولاً (إذا كانت النتائج معروضة من البداية)
    setTimeout(() => {
      animateConfidenceBars();
    }, 50); // تأخير بسيط

});