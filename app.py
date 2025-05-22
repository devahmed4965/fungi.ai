from flask import Flask, request, render_template, flash, send_from_directory, redirect, url_for, make_response, g, session
import os
os.environ["TF_USE_DIRECTML"] = "0"

import tensorflow as tf
from tensorflow.keras.preprocessing import image
from werkzeug.utils import secure_filename
import numpy as np
import os
import uuid
import logging
from typing import Dict, Any, Tuple, Optional
from flask_babel import Babel, _


# إعداد التسجيل الأساسي
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
# !!! هام: غير هذا المفتاح في بيئة الإنتاج !!! استخدم مفتاحًا عشوائيًا وقويًا
# IMPORTANT: Change this key in production environment! Use a random and strong key
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change_this_to_a_strong_random_secret_key")
app.config['UPLOAD_FOLDER'] = 'uploads'
# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- قاموس التصنيف العلمي الموسع ---
# --- Extended Scientific Taxonomy Dictionary ---
taxonomy_map: Dict[str, Dict[str, Any]] = {
    'Amanita': {
        'Domain': {'en': 'Eukaryota', 'ar': 'حقيقيات النوى'},
        'Kingdom': {'en': 'Fungi', 'ar': 'فطريات'},
        'Phylum': {'en': 'Basidiomycota', 'ar': 'فطريات بازيدية'},
        'Class': {'en': 'Agaricomycetes', 'ar': 'أغاريقونيات'},
        'Order': {'en': 'Agaricales', 'ar': 'غاريقونيات'},
        'Family': {'en': 'Amanitaceae', 'ar': 'أمانيتية'},
        'Genus': {'en': 'Amanita', 'ar': 'أمانيت'},
        'Species': {'en': 'Unspecified', 'ar': 'غير محدد'},
        'Toxicity': {'en': 'Deadly to Highly Toxic', 'ar': 'سامة إلى شديدة السمية'},
        'Edibility': {'en': 'Inedible', 'ar': 'غير صالح للأكل'},
        'Uses': {'en': 'Research (toxins), limited medicinal use', 'ar': 'بحث (سموم)، استخدام طبي محدود'},
        'Cultivation': {'en': 'Mycorrhizal (not cultivated)', 'ar': 'متكافل جذر (غير مستزرع)'},
        'Cultivation_Details': {
            'Substrate': {'en': 'Mycorrhizal with various trees', 'ar': 'متكافل جذر مع أشجار متنوعة'},
            'Conditions': {'en': 'Temperate and boreal forests', 'ar': 'غابات معتدلة وشمالية'},
            'Timeline': {'en': 'Summer to autumn', 'ar': 'الصيف إلى الخريف'},
            'Yield': {'en': 'Not applicable', 'ar': 'غير قابل للتطبيق'}
        },
        'Nutritional_Info': {
            'Benefits': {'en': 'None', 'ar': 'لا شيء'},
            'Risks': {'en': 'Contains amatoxins and phallotoxins, causing severe liver and kidney damage',
                     'ar': 'يحتوي على أماتوكسين وفالوتوكسين، يسبب تلفًا شديدًا في الكبد والكلى'}
        },
        'Additional_Info': {'en': 'Includes Death Cap and Destroying Angel. Expert identification is crucial.',
                            'ar': 'يشمل قبعة الموت والملاك المدمر. التشخيص المتخصص ضروري للغاية.'}
    },
    'Agaricus': {
        'Domain': {'en': 'Eukaryota', 'ar': 'حقيقيات النوى'},
        'Kingdom': {'en': 'Fungi', 'ar': 'فطريات'},
        'Phylum': {'en': 'Basidiomycota', 'ar': 'فطريات بازيدية'},
        'Class': {'en': 'Agaricomycetes', 'ar': 'أغاريقونيات'},
        'Order': {'en': 'Agaricales', 'ar': 'غاريقونيات'},
        'Family': {'en': 'Agaricaceae', 'ar': 'غاريقية'},
        'Genus': {'en': 'Agaricus', 'ar': 'غاريقون'},
        'Species': {'en': 'Unspecified', 'ar': 'غير محدد'},
        'Toxicity': {'en': 'Variable', 'ar': 'متغير'},
        'Edibility': {'en': 'Variable', 'ar': 'متغير'},
        'Uses': {'en': 'Culinary', 'ar': 'طهوي'},
        'Cultivation': {'en': 'Cultivated', 'ar': 'مستزرع'},
        'Cultivation_Details': {
            'Substrate': {'en': 'Composted materials', 'ar': 'مواد متحللة'},
            'Conditions': {'en': 'Controlled environment', 'ar': 'بيئة محكومة'},
            'Timeline': {'en': 'Weeks', 'ar': 'أسابيع'},
            'Yield': {'en': 'High', 'ar': 'عالي'}
        },
        'Nutritional_Info': {
            'Benefits': {'en': 'Protein, B vitamins', 'ar': 'بروتين، فيتامينات ب'},
            'Risks': {'en': 'Some species are toxic', 'ar': 'بعض الأنواع سامة'}
        },
        'Additional_Info': {'en': 'Button mushroom is a common species.', 'ar': 'فطر الأزرار نوع شائع.'}
    },
    'Boletus': {
        'Domain': {'en':'Eukaryota', 'ar':'حقيقيات النوى'},
        'Kingdom': {'en':'Fungi', 'ar':'فطريات'},
        'Phylum': {'en':'Basidiomycota', 'ar':'فطريات بازيدية'},
        'Class': {'en':'Agaricomycetes', 'ar':'أغاريقونيات'},
        'Order': {'en':'Boletales', 'ar':'بوليطيات'},
        'Family': {'en':'Boletaceae', 'ar':'بوليطية'},
        'Genus': {'en':'Boletus', 'ar':'بوليط'},
        'Species': {'en':'Unspecified', 'ar':'غير محدد'},
        'Toxicity': {'en':'Variable (some edible, some toxic)', 'ar':'متنوع (بعضها صالح للأكل، وبعضها سام)'},
        'Edibility': {'en':'Variable (some choice edible, some toxic)', 'ar':'متنوع (بعضها المفضل، وبعضها سام)'},
        'Uses': {'en':'Culinary (many choice edibles), research', 'ar':'طهوي (العديد من الأنواع المفضلة)، بحث'},
        'Cultivation': {'en':'Mycorrhizal (not cultivated commercially)', 'ar':'متكافل جذر (غير مستزرع تجارياً)'},
        'Cultivation_Details': {
            'Substrate': {'en':'Mycorrhizal with roots of various trees (e.g., pine, oak, birch)', 'ar':'متكافل جذر مع جذور أشجار متنوعة (مثل الصنوبر والبلوط والبتولا)'},
            'Conditions': {'en':'Found in forests, often associated with specific tree species', 'ar':'يوجد في الغابات، وغالباً ما يرتبط بأنواع معينة من الأشجار'},
            'Timeline': {'en':'Fruiting in summer and autumn, depending on species and location', 'ar':'يثمر في الصيف والخريف، حسب النوع والموقع'},
            'Yield': {'en':'Variable, dependent on environmental conditions', 'ar':'متنوع، ويعتمد على الظروف البيئية'}
           },
           'Nutritional_Info': {
               'Benefits': {'en':'Edible boletes are prized for their flavor and texture. Good source of protein and some vitamins and minerals.', 'ar':'يشتهر البوليط الصالح للأكل بنكهته وملمسه. مصدر جيد للبروتين وبعض الفيتامينات والمعادن.'},
               'Risks': {'en':'Some Boletus species are toxic, causing gastrointestinal distress. Can be confused with bitter or unpalatable species. *Boletus edulis* and similar species are safe, but others, like *Boletus satanas*, are poisonous. **Careful identification is essential.**', 'ar':'بعض أنواع البوليط سامة، وتسبب ضائقة معوية. يمكن الخلط بين بعضها وبين الأنواع المرة أو غير المستساغة. *Boletus edulis* وأنواع مشابهة آمنة، ولكن أنواع أخرى، مثل *Boletus satanas*، سامة. **التشخيص الدقيق ضروري.**'}
           },
           'Additional_Info': {'en':'Boletes are characterized by pores instead of gills. Many are choice edibles, but some are toxic. Only experienced mushroom hunters should collect wild boletes.', 'ar':'يتميز البوليط بوجود مسام بدلاً من الخياشيم. العديد منها من الأنواع المفضلة، ولكن بعضها سام. يجب على صائدي الفطر المتمرسين فقط جمع البوليط البري.'}
       },
    'Cantharellus': {
        'Domain': {'en': 'Eukaryota', 'ar': 'حقيقيات النوى'},
        'Kingdom': {'en': 'Fungi', 'ar': 'فطريات'},
        'Phylum': {'en': 'Basidiomycota', 'ar': 'فطريات بازيدية'},
        'Class': {'en': 'Agaricomycetes', 'ar': 'أغاريقونيات'},
        'Order': {'en': 'Cantharellales', 'ar': 'كانثريليات'},
        'Family': {'en': 'Cantharellaceae', 'ar': 'كانثريلية'},
        'Genus': {'en': 'Cantharellus', 'ar': 'كانثريلوس'},
        'Species': {'en': 'Unspecified', 'ar': 'غير محدد'},
        'Toxicity': {'en': 'Generally Non-toxic', 'ar': 'غير سام بشكل عام'},
        'Edibility': {'en': 'Edible (choice)', 'ar': 'صالح للأكل (مفضل)'},
        'Uses': {'en': 'Culinary', 'ar': 'طهوي'},
        'Cultivation': {'en': 'Mycorrhizal (not cultivated commercially)', 'ar': 'متكافل جذر (غير مستزرع تجارياً)'},
        'Cultivation_Details': {
            'Substrate': {'en': 'Mycorrhizal with trees', 'ar': 'متكافل جذر مع الأشجار'},
            'Conditions': {'en': 'Forests', 'ar': 'غابات'},
            'Timeline': {'en': 'Summer and autumn', 'ar': 'الصيف والخريف'},
            'Yield': {'en': 'Moderate', 'ar': 'متوسط'}
        },
        'Nutritional_Info': {
            'Benefits': {'en': 'Good flavor and aroma', 'ar': 'نكهة ورائحة جيدة'},
            'Risks': {'en': 'Can be confused with false chanterelles', 'ar': 'يمكن الخلط بينه وبين الشانتريل الزائف'}
        },
        'Additional_Info': {'en': 'Chanterelles are prized edible mushrooms.', 'ar': 'الشنترelles من الفطريات الصالحة للأكل.'}
    },
    'Lactarius': {
        'Domain': {'en': 'Eukaryota', 'ar': 'حقيقيات النوى'},
        'Kingdom': {'en': 'Fungi', 'ar': 'فطريات'},
        'Phylum': {'en': 'Basidiomycota', 'ar': 'فطريات بازيدية'},
        'Class': {'en': 'Agaricomycetes', 'ar': 'أغاريقونيات'},
        'Order': {'en': 'Russulales', 'ar': 'روسوليات'},
        'Family': {'en': 'Russulaceae', 'ar': 'روسولية'},
        'Genus': {'en': 'Lactarius', 'ar': 'لاكتاريوس'},
        'Species': {'en': 'Unspecified', 'ar': 'غير محدد'},
        'Toxicity': {'en': 'Variable (some edible, some toxic)', 'ar': 'متنوع (بعضها صالح للأكل، وبعضها سام)'},
        'Edibility': {'en': 'Variable (some edible, some toxic)', 'ar': 'متنوع (بعضها صالح للأكل، وبعضها سام)'},
        'Uses': {'en': 'Culinary (some species, after preparation)', 'ar': 'طهوي (بعض الأنواع، بعد التحضير)'},
        'Cultivation': {'en': 'Mycorrhizal (not cultivated)', 'ar': 'متكافل جذر (غير مستزرع)'},
        'Cultivation_Details': {
            'Substrate': {'en': 'Mycorrhizal with trees', 'ar': 'متكافل جذر مع الأشجار'},
            'Conditions': {'en': 'Forests', 'ar': 'غابات'},
            'Timeline': {'en': 'Summer and autumn', 'ar': 'الصيف والخريف'},
            'Yield': {'en': 'Variable', 'ar': 'متنوع'}
        },
        'Nutritional_Info': {
            'Benefits': {'en': 'Some species are edible after cooking', 'ar': 'بعض الأنواع صالحة للأكل بعد الطهي'},
            'Risks': {'en': 'Many species are bitter or acrid', 'ar': 'العديد من الأنواع مر أو حريف'}
        },
        'Additional_Info': {'en': 'Lactarius mushrooms exude a milky latex.', 'ar': 'فطر Lactarius يفرز مادة لبنية.'}
    },
    'Ganoderma': {
        'Domain': {'en': 'Eukaryota', 'ar': 'حقيقيات النوى'},
        'Kingdom': {'en': 'Fungi', 'ar': 'فطريات'},
        'Phylum': {'en': 'Basidiomycota', 'ar': 'فطريات بازيدية'},
        'Class': {'en': 'Agaricomycetes', 'ar': 'أغاريقونيات'},
        'Order': {'en': 'Polyporales', 'ar': 'بوليبوراليس'},
        'Family': {'en': 'Ganodermataceae', 'ar': 'جانوديرماتاسيا'},
        'Genus': {'en': 'Ganoderma', 'ar': 'جانوديرما'},
        'Species': {'en': 'Unspecified', 'ar': 'غير محدد'},
        'Toxicity': {'en': 'Non-toxic', 'ar': 'غير سام'},
        'Edibility': {'en': 'Medicinal', 'ar': 'طبي'},
        'Uses': {'en': 'Medicinal', 'ar': 'طبي'},
        'Cultivation': {'en': 'Cultivated', 'ar': 'مستزرع'},
        'Cultivation_Details': {
            'Substrate': {'en': 'Hardwood logs or sawdust', 'ar': 'سجلات أو نشارة خشب صلب'},
            'Conditions': {'en': 'Controlled environment', 'ar': 'بيئة محكومة'},
            'Timeline': {'en': 'Months', 'ar': 'أشهر'},
            'Yield': {'en': 'Moderate', 'ar': 'متوسط'}
           },
           'Nutritional_Info': {
               'Benefits': {'en': 'Potential immune-boosting effects', 'ar': 'تأثيرات محتملة لتعزيز المناعة'},
               'Risks': {'en': 'Rare allergic reactions', 'ar': 'ردود فعل تحسسية نادرة'}
           },
           'Additional_Info': {'en': 'Ganoderma are polypores used for medicinal purposes.', 'ar': 'Ganoderma هي متعددات المسام تستخدم للأغراض الطبية.'}
       },
       'Trametes': {
           'Domain': {'en': 'Eukaryota', 'ar': 'حقيقيات النوى'},
           'Kingdom': {'en': 'Fungi', 'ar': 'فطريات'},
           'Phylum': {'en': 'Basidiomycota', 'ar': 'فطريات بازيدية'},
           'Class': {'en': 'Agaricomycetes', 'ar': 'أغاريقونيات'},
           'Order': {'en': 'Polyporales', 'ar': 'بوليبوراليس'},
           'Family': {'en': 'Polyporaceae', 'ar': 'بوليبوراسيا'},
           'Genus': {'en': 'Trametes', 'ar': 'تراميتس'},
           'Species': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Toxicity': {'en': 'Non-toxic', 'ar': 'غير سام'},
           'Edibility': {'en': 'Inedible', 'ar': 'غير صالح للأكل'},
           'Uses': {'en': 'Research (enzymes)', 'ar': 'بحث (إنزيمات)'},
           'Cultivation': {'en': 'Cultivated (for enzymes)', 'ar': 'مستزرع (للإنزيمات)'},
           'Cultivation_Details': {
               'Substrate': {'en': 'Wood logs or sawdust', 'ar': 'سجلات أو نشارة خشب'},
               'Conditions': {'en': 'Controlled environment', 'ar': 'بيئة محكومة'},
               'Timeline': {'en': 'Weeks to months', 'ar': 'أسابيع إلى أشهر'},
               'Yield': {'en': 'Moderate', 'ar': 'متوسط'}
           },
           'Nutritional_Info': {
               'Benefits': {'en': 'Source of enzymes', 'ar': 'مصدر للإنزيمات'},
               'Risks': {'en': 'Not typically consumed as food', 'ar': 'لا تستهلك عادة كغذاء'}
           },
           'Additional_Info': {'en': 'Trametes are thin, tough polypores.', 'ar': 'Trametes هي متعددات مسام رقيقة وصلبة.'},
       },
       'Russula': {
           'Domain': {'en': 'Eukaryota', 'ar': 'حقيقيات النوى'},
           'Kingdom': {'en': 'Fungi', 'ar': 'فطريات'},
           'Phylum': {'en': 'Basidiomycota', 'ar': 'فطريات بازيدية'},
           'Class': {'en': 'Agaricomycetes', 'ar': 'أغاريقونيات'},
           'Order': {'en': 'Russulales', 'ar': 'روسوليات'},
           'Family': {'en': 'Russulaceae', 'ar': 'روسولية'},
           'Genus': {'en': 'Russula', 'ar': 'روسولا'},
           'Species': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Toxicity': {'en': 'Variable (some edible, some toxic)', 'ar': 'متنوع (بعضها صالح للأكل، وبعضها سام)'},
           'Edibility': {'en': 'Variable (some edible, some toxic)', 'ar': 'متنوع (بعضها صالح للأكل، وبعضها سام)'},
           'Uses': {'en': 'Culinary (some species)', 'ar': 'طهوي (بعض الأنواع)'},
           'Cultivation': {'en': 'Mycorrhizal (not cultivated)', 'ar': 'متكافل جذر (غير مستزرع)'},
           'Cultivation_Details': {
               'Substrate': {'en': 'Mycorrhizal with trees', 'ar': 'متكافل جذر مع الأشجار'},
               'Conditions': {'en': 'Forests', 'ar': 'غابات'},
               'Timeline': {'en': 'Summer and autumn', 'ar': 'الصيف والخريف'},
               'Yield': {'en': 'Variable', 'ar': 'متنوع'}
           },
           'Nutritional_Info': {
               'Benefits': {'en': 'Some species are edible', 'ar': 'بعض الأنواع صالحة للأكل'},
               'Risks': {'en': 'Many species are unpalatable', 'ar': 'العديد من الأنواع غير مستساغة'}
           },
           'Additional_Info': {'en': 'Russula are brittle and diverse.', 'ar': 'Russula هشة ومتنوعة.'}
       },
       'Pezizales': {
           'Domain': {'en': 'Eukaryota', 'ar': 'حقيقيات النوى'},
           'Kingdom': {'en': 'Fungi', 'ar': 'فطريات'},
           'Phylum': {'en': 'Ascomycota', 'ar': 'فطريات زقية'},
           'Class': {'en': 'Pezizomycetes', 'ar': 'بيزيزوميستس'},
           'Order': {'en': 'Pezizales', 'ar': 'بيزيزاليس'},
           'Family': {'en': 'Multiple', 'ar': 'متعددة'},
           'Genus': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Species': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Toxicity': {'en': 'Variable (some edible, some toxic)', 'ar': 'متنوع (بعضها صالح للأكل، وبعضها سام)'},
           'Edibility': {'en': 'Variable (some edible, some toxic)', 'ar': 'متنوع (بعضها صالح للأكل، وبعضها سام)'},
           'Uses': {'en': 'Culinary (truffles)', 'ar': 'طهوي (الكمأ)'},
           'Cultivation': {'en': 'Cultivated (truffles)', 'ar': 'مستزرع (الكمأ)'},
           'Cultivation_Details': {
               'Substrate': {'en': 'Mycorrhizal with tree roots (truffles)', 'ar': 'متكافل جذر مع جذور الأشجار (الكمأ)'},
               'Conditions': {'en': 'Varies greatly', 'ar': 'يختلف بشكل كبير'},
               'Timeline': {'en': 'Varies greatly', 'ar': 'يختلف بشكل كبير'},
               'Yield': {'en': 'Variable', 'ar': 'متنوع'}
           },
           'Nutritional_Info': {
               'Benefits': {'en': 'Truffles are prized for flavor', 'ar': 'يشتهر الكمأ بنكهته'},
               'Risks': {'en': 'Some species may be inedible', 'ar': 'بعض الأنواع قد تكون غير صالحة للأكل'}
           },
           'Additional_Info': {'en': 'Pezizales are cup fungi. Includes truffles.', 'ar': 'Pezizales هي فنجانيات. تشمل الكمأ.'}
       },
       'Erysiphales': {
           'Domain': {'en': 'Eukaryota', 'ar': 'حقيقيات النوى'},
           'Kingdom': {'en': 'Fungi', 'ar': 'فطريات'},
           'Phylum': {'en': 'Ascomycota', 'ar': 'فطريات زقية'},
           'Class': {'en': 'Leotiomycetes', 'ar': 'ليوتيوميسيتس'},
           'Order': {'en': 'Erysiphales', 'ar': 'إريسيفاليس'},
           'Family': {'en': 'Erysiphaceae', 'ar': 'إريسيفاسيا'},
           'Genus': {'en': 'Multiple (e.g., Erysiphe, Podosphaera)', 'ar': 'متعددة (مثل Erysiphe, Podosphaera)'},
           'Species': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Toxicity': {'en': 'Non-toxic', 'ar': 'غير سام'},
           'Edibility': {'en': 'Inedible', 'ar': 'غير صالح للأكل'},
           'Uses': {'en': 'None', 'ar': 'لا شيء'},
           'Cultivation': {'en': 'Not applicable', 'ar': 'غير قابل للتطبيق'},
           'Cultivation_Details': {
               'Substrate': {'en': 'Living plant tissue', 'ar': 'أنسجة نباتية حية'},
               'Conditions': {'en': 'Varies with host plant', 'ar': 'يختلف باختلاف النبات المضيف'},
               'Timeline': {'en': 'Rapid life cycle', 'ar': 'دورة حياة سريعة'},
               'Yield': {'en': 'Not applicable', 'ar': 'غير قابل للتطبيق'}
           },
           'Nutritional_Info': {
               'Benefits': {'en': 'None', 'ar': 'لا شيء'},
               'Risks': {'en': 'Cause plant diseases', 'ar': 'يسبب أمراض النباتات'}
           },
           'Additional_Info': {'en': 'Powdery mildew fungi.', 'ar': 'فطريات البياض الدقيقي.'}
       },
       'Saccharomycetales': {
           'Domain': {'en': 'Eukaryota', 'ar': 'حقيقيات النوى'},
           'Kingdom': {'en': 'Fungi', 'ar': 'فطريات'},
           'Phylum': {'en': 'Ascomycota', 'ar': 'فطريات زقية'},
           'Class': {'en': 'Saccharomycetes', 'ar': 'ساكاروميسيتس'},
           'Order': {'en': 'Saccharomycetales', 'ar': 'ساكاروميسيتاليس'},
           'Family': {'en': 'Multiple (e.g., Saccharomycetaceae)', 'ar': 'متعددة (مثل Saccharomycetaceae)'},
           'Genus': {'en': 'Multiple (e.g., Saccharomyces)', 'ar': 'متعددة (مثل Saccharomyces)'},
           'Species': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Toxicity': {'en': 'Non-toxic', 'ar': 'غير سام'},
           'Edibility': {'en': 'Edible (some species)', 'ar': 'صالح للأكل (بعض الأنواع)'},
           'Uses': {'en': 'Industrial (fermentation), Culinary', 'ar': 'صناعي (تخمير)، طهوي'},
           'Cultivation': {'en': 'Cultivated', 'ar': 'مستزرع'},
           'Cultivation_Details': {
               'Substrate': {'en': 'Sugars, grains', 'ar': 'سكريات، حبوب'},
               'Conditions': {'en': 'Controlled fermentation', 'ar': 'تخمير محكوم'},
               'Timeline': {'en': 'Rapid growth', 'ar': 'نمو سريع'},
               'Yield': {'en': 'High', 'ar': 'عالي'}
           },
           'Nutritional_Info': {
               'Benefits': {'en': 'Yeast is a source of B vitamins', 'ar': 'الخميرة مصدر لفيتامينات ب'},
               'Risks': {'en': 'None', 'ar': 'لا شيء'}
           },
           'Additional_Info': {'en': 'Yeasts used in baking and brewing.', 'ar': 'خمائر تستخدم في الخبز والتخمير.'}
       },
       'Glomeromycota': {
           'Domain': {'en': 'Eukaryota', 'ar': 'حقيقيات النوى'},
           'Kingdom': {'en': 'Fungi', 'ar': 'فطريات'},
           'Phylum': {'en': 'Glomeromycota', 'ar': 'جلوميروميكوتا'},
           'Class': {'en': 'Multiple', 'ar': 'متعددة'},
           'Order': {'en': 'Multiple', 'ar': 'متعددة'},
           'Family': {'en': 'Multiple', 'ar': 'متعددة'},
           'Genus': {'en': 'Multiple (e.g., Glomus)', 'ar': 'متعددة (مثل Glomus)'},
           'Species': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Toxicity': {'en': 'Non-toxic', 'ar': 'غير سام'},
           'Edibility': {'en': 'Not applicable', 'ar': 'غير قابل للتطبيق'},
           'Uses': {'en': 'Ecological (plant symbiosis)', 'ar': 'بيئي (تكافل نباتي)'},
           'Cultivation': {'en': 'Mycorrhizal (not cultivated)', 'ar': 'متكافل جذر (غير مستزرع)'},
           'Cultivation_Details': {
               'Substrate': {'en': 'Roots of plants', 'ar': 'جذور النباتات'},
               'Conditions': {'en': 'Soil', 'ar': 'تربة'},
               'Timeline': {'en': 'Lifelong symbiosis', 'ar': 'تكافل مدى الحياة'},
               'Yield': {'en': 'N/A', 'ar': 'غير قابل للتطبيق'}
           },
           'Nutritional_Info': {
               'Benefits': {'en': 'Enhance plant growth', 'ar': 'يعزز نمو النبات'},
               'Risks': {'en': 'None', 'ar': 'لا شيء'}
           },
           'Additional_Info': {'en': 'Form mycorrhizae with plant roots.', 'ar': 'تشكل ميكورهيزا مع جذور النباتات.'}
       },
       'Others': {
           'Domain': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Kingdom': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Phylum': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Class': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Order': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Family': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Genus': {'en': 'Unspecified', 'ar': 'غير محدد'},
           'Species': {'en': 'Other/Unclassified', 'ar': 'أخرى/غير مصنف'},
           'Toxicity': {'en': 'Variable', 'ar': 'متغير'},
           'Edibility': {'en': 'Variable', 'ar': 'متغير'},
           'Uses': {'en': 'Variable', 'ar': 'متغير'},
           'Cultivation': {'en': 'Variable', 'ar': 'متغير'},
           'Cultivation_Details': {
               'Substrate': {'en': 'Variable', 'ar': 'متغير'},
               'Conditions': {'en': 'Variable', 'ar': 'متغير'},
               'Timeline': {'en': 'Variable', 'ar': 'متغير'},
               'Yield': {'en': 'Variable', 'ar': 'متغير'}
           },
           'Nutritional_Info': {
               'Benefits': {'en': 'Variable', 'ar': 'متغير'},
               'Risks': {'en': 'Variable', 'ar': 'متغير'}
           },
           'Additional_Info': {'en': 'For unidentifiable images.', 'ar': 'للصور غير القابلة للتحديد.'}
       }
    }

MODEL_BASENAME = "VGG16"
MODEL_PATH = os.path.join('models', 'fungal_classifier_VGG16_best.h5')
model = None
model_output_units = -1

# Attempt to load the TensorFlow model
try:
    if os.path.exists(MODEL_PATH):
        model = tf.keras.models.load_model(MODEL_PATH)
        logging.info(f"Model loaded successfully from {MODEL_PATH}")
        try:
            # Get the number of output units (classes) from the loaded model
            output_shape = model.output_shape
            model_output_units = output_shape[-1]
            logging.info(f"Loaded model expects {model_output_units} output units (classes).")
        except Exception as shape_e:
            logging.warning(f"Could not determine model output shape automatically: {shape_e}")
    else:
        logging.error(f"Error: Model file not found at {MODEL_PATH}")
except Exception as e:
    logging.exception(f"Critical Error loading model from {MODEL_PATH}: {e}")
    model = None # Ensure model is None if loading fails

# Get class labels from the taxonomy map keys and sort them
class_labels = sorted(list(taxonomy_map.keys()))
logging.info(f"Class labels based on taxonomy map (sorted): {class_labels}")
num_expected_classes = len(class_labels)
logging.info(f"Number of classes expected by app based on taxonomy map: {num_expected_classes}")

# Check for mismatch between model output units and taxonomy map classes
if model is not None and model_output_units != -1 and model_output_units != num_expected_classes:
    logging.error("###########################################################################")
    logging.error(f"CRITICAL MISMATCH DETECTED ON LOAD:")
    logging.error(f"  Model output units: {model_output_units}")
    logging.error(f"  Classes in taxonomy_map: {num_expected_classes}")
    logging.error(" Please CORRECT the taxonomy_map in app.py to match the model!")
    logging.error("###########################################################################")


EXPECTED_IMG_SIZE = (224, 224) # Expected image size for the model

# Babel configuration for internationalization (i18n)
def get_locale() -> str:
    # Determine the user's preferred locale.
    # This simple example uses the 'lang' query parameter or session, defaulting to 'ar'.
    # A real app might use request.accept_languages, user settings, etc.
    lang = session.get('lang', 'ar')
    logging.debug(f"Determined locale: {lang}")
    return lang

babel = Babel(app, locale_selector=get_locale)

# Route for file upload and classification
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    # Set language based on query param or session, default to Arabic
    g.lang = request.args.get('lang', session.get('lang', 'ar'))
    if g.lang not in ['en', 'ar']:
        g.lang = 'ar' # Fallback to Arabic if invalid lang is provided
    session['lang'] = g.lang # Store language preference in session
    logging.debug(f"Current request language set to: {g.lang}")

    # Initialize variables for template rendering
    image_url_display = None
    predictions_display = []
    full_taxonomy_display = None
    taxonomy_message = None

    if request.method == 'POST':
        # Check if the model was loaded successfully
        if model is None:
            flash(_('خطأ حرج: نموذج التصنيف غير مُحمّل. لا يمكن المتابعة. يرجى مراجعة سجلات الخادم.'), 'error')
            logging.error("Model is None during POST request.")
            return render_template('upload.html', class_labels=class_labels)

        # Check if the 'file' part is in the request
        if 'file' not in request.files:
            flash(_('لم يتم إرفاق أي ملف.'), 'warning')
            logging.warning("No file part in request.")
            return redirect(request.url)

        file = request.files['file']
        # Check if a file was selected
        if file.filename == '':
            flash(_('لم يتم اختيار ملف.'), 'warning')
            logging.warning("No selected file.")
            return redirect(request.url)

        # Validate file extension
        allowed_extensions = {'png', 'jpg', 'jpeg'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            flash(_('نوع الملف غير مسموح به. يرجى رفع صورة بامتداد png, jpg, أو jpeg.'), 'error')
            logging.warning(f"Disallowed file extension: {file_ext}")
            return redirect(request.url)

        try:
            # Secure filename and save the file
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            logging.info(f"File saved to: {file_path}")
            image_url_display = filename # URL to display the image

            # Load and preprocess the image for the model
            img = image.load_img(file_path, target_size=EXPECTED_IMG_SIZE)
            img_array = image.img_to_array(img)
            img_array_scaled = img_array / 255.0 # Scale pixel values
            img_batch = np.expand_dims(img_array_scaled, axis=0) # Add batch dimension

            logging.info(f"Predicting using model: {MODEL_PATH}")
            # Perform prediction
            preds_raw = model.predict(img_batch)[0]
            logging.info(f"Model produced {len(preds_raw)} probability outputs.")

            # Check if the number of model outputs matches the number of classes
            if len(preds_raw) != num_expected_classes:
                error_msg = (f'خطأ في التوافق: النموذج أخرج {len(preds_raw)} احتمالات، '
                             f'بينما القائمة المتوقعة تحتوي على {num_expected_classes} فئات ({class_labels}). '
                             f'هل تم تحديث taxonomy_map في app.py بشكل صحيح ليشمل جميع الفئات الـ {len(preds_raw)} التي يعرفها النموذج؟')
                flash(error_msg, 'error')
                logging.error(error_msg)
                # Clean up the uploaded file if there's a mismatch
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logging.info(f"Removed file {file_path} due to model/class mismatch error.")
                return redirect(request.url)

            # Process predictions: pair with labels, sort, and format confidence
            predictions_data = [{'class': label, 'confidence': f"{prob * 100:.2f}%"} for label, prob in zip(class_labels, preds_raw)]
            predictions_data.sort(key=lambda x: x['confidence'], reverse=True) # Sort by confidence descending

            # Determine the top prediction label
            top_prediction_label = None
            if predictions_data:
                top_prediction_label = predictions_data[0]['class']
                try:
                    confidence = float(predictions_data[0]['confidence'].replace('%', ''))
                    logging.info(f"Top prediction: {top_prediction_label} ({confidence:.2f}%)")
                except ValueError:
                    logging.error(f"Confidence value is not a valid number: {predictions_data[0]['confidence']}")
                    confidence = 0.0  # Or some default value
                    logging.info(f"Top prediction: {top_prediction_label} (Confidence unavailable)")
                # Mark the top prediction for highlighting in the template
                predictions_data[0]['is_top'] = True
                for i in range(1, len(predictions_data)):
                    predictions_data[i]['is_top'] = False

            # Select top 5 predictions to display
            predictions_display = [
                {
                    'class': pred_data['class'],
                    'confidence':  pred_data['confidence'],
                    'is_top': pred_data.get('is_top', False)
                }
                for pred_data in predictions_data[:5]
            ]

            # Retrieve and translate full taxonomy information for the top prediction
            if top_prediction_label:
                full_taxonomy_raw = taxonomy_map.get(top_prediction_label)
                if full_taxonomy_raw is None:
                    taxonomy_message = f"لم يتم العثور على معلومات تصنيف للفئة المتوقعة '{top_prediction_label}' في القاموس."
                    logging.warning(taxonomy_message)
                elif not isinstance(full_taxonomy_raw, dict):
                    error_msg = f"خطأ في البيانات: قيمة التصنيف لـ '{top_prediction_label}' ليست قاموسًا."
                    taxonomy_message = error_msg
                    logging.error(error_msg)
                    full_taxonomy_display = None # Ensure it's None if data is malformed
                else:
                    # Translate taxonomy details based on the current language (g.lang)
                    translated_taxonomy = {}
                    for key, value in full_taxonomy_raw.items():
                        # Handle nested dictionaries for Cultivation_Details and Nutritional_Info
                        if key in ['Cultivation_Details', 'Nutritional_Info'] and isinstance(value, dict):
                            nested = {}
                            for subkey, subval in value.items():
                                if isinstance(subval, dict):
                                    # Get translation, fallback to English, then empty string
                                    nested[subkey] = subval.get(g.lang, subval.get('en', ''))
                                else:
                                     # If not a dict (shouldn't happen based on taxonomy_map structure), use value directly
                                    nested[subkey] = subval
                            translated_taxonomy[key] = nested
                        elif isinstance(value, dict):
                            # Get translation for top-level keys, fallback to English, then empty string
                            translated_taxonomy[key] = value.get(g.lang, value.get('en', ''))
                        else:
                            # If value is not a dict (shouldn't happen), use value directly
                            translated_taxonomy[key] = value
                    full_taxonomy_display = translated_taxonomy
            else:
                taxonomy_message = "لم يتم تحديد فئة ذات ثقة كافية للحصول على التصنيف."
                logging.info("No top prediction with sufficient confidence to retrieve taxonomy.")


        # Handle potential errors during file processing or prediction
        except FileNotFoundError:
            flash(_('خطأ: الملف الذي تم تحميله لم يتم العثور عليه للمعالجة.'), 'error')
            logging.error(f"File not found after saving: {file_path}")
            # No need to remove file here, as it wasn't found anyway
            return redirect(request.url)
        except Exception as e:
            logging.exception(f'حدث خطأ غير متوقع أثناء معالجة الملف {file.filename}: {e}')
            flash(_('حدث خطأ أثناء معالجة الصورة. يرجى المحاولة مرة أخرى أو مراجعة السجلات.'), 'error')
            # Attempt to remove the problematic file
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logging.info(f"Removed corrupted/problematic file: {file_path}")
                except OSError as remove_error:
                    logging.error(f"Error removing file {file_path}: {remove_error}")
            # Render the template with error message and no results
            return render_template('upload.html', image_url=None, predictions=[], full_taxonomy=None,
                                   taxonomy_message="فشلت معالجة الصورة.", class_labels=class_labels)

    # Render the template for GET requests or after POST processing
    return render_template(
        'upload.html', image_url=image_url_display, predictions=predictions_display,
        full_taxonomy=full_taxonomy_display, taxonomy_message=taxonomy_message, class_labels=class_labels
    )

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        # Serve the file from the upload folder
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        logging.warning(f"Attempted to access non-existent file: {filename}")
        return "File not found", 404 # Return 404 if file doesn't exist

# Run the Flask application
if __name__ == '__main__':
    # Running in debug mode for development.
    # In production, use a production-ready WSGI server like Gunicorn or uWSGI.
    # Also, ensure FLASK_SECRET_KEY is set securely in the environment.
      app.run(debug=True, host='0.0.0.0', port=5001)