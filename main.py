import cv2
import numpy as np
import time
import serial
import os
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display



WIDTH, HEIGHT = 1024, 768
COM_PORT = 'COM4'

DRAW_DURATION = 12.0
FLAG_DURATION = 36.0

LYRICS_END = 48.0

WINDOW_NAME = "Saudi Layered Painting Transition"



FLAG_X = 0
FLAG_Y = 0

FLAG_W = int(WIDTH * 0.50)
FLAG_H = int(HEIGHT * 0.60)



def send_signal_to_arduino(port):

    try:

        ser = serial.Serial(
            port,
            9600,
            timeout=1
        )

        # انتظار إعادة تشغيل Arduino
        time.sleep(2)

        ser.write(b'1')

        print(
            f"[+] تم إرسال إشارة التفعيل إلى Arduino "
            f"على المنفذ {port}"
        )

        ser.close()

    except Exception as e:

        print(
            f"[-] تعذر الاتصال بـ Arduino: {e}"
        )


# ==========================================
# 4. إنشاء الخط العربي
# ==========================================

def get_system_arabic_font(font_size=55):

    font_paths = [

        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\trado.ttf",
        "C:\\Windows\\Fonts\\tahoma.ttf",
        "C:\\Windows\\Fonts\\segoeui.ttf"

    ]

    for path in font_paths:

        if os.path.exists(path):

            try:

                return ImageFont.truetype(
                    path,
                    font_size
                )

            except Exception:
                continue

    return ImageFont.load_default()


# ==========================================
# 5. إنشاء صورة النص العربي
# ==========================================

def create_arabic_text_image(text):

    reshaped_text = arabic_reshaper.reshape(text)

    bidi_text = get_display(
        reshaped_text
    )

    pil_image = Image.new(
        'L',
        (WIDTH, HEIGHT),
        color=0
    )

    draw = ImageDraw.Draw(
        pil_image
    )

    font = get_system_arabic_font(
        font_size=52
    )

    bbox = draw.textbbox(
        (0, 0),
        bidi_text,
        font=font
    )

    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x_pos = (
        WIDTH - text_w
    ) // 2

    y_pos = (
        HEIGHT - text_h - 45
    )

    draw.text(
        (x_pos, y_pos),
        bidi_text,
        font=font,
        fill=255
    )

    mask = np.array(
        pil_image
    )

    # لون النص
    text_color_layer = np.zeros(
        (HEIGHT, WIDTH, 3),
        dtype=np.uint8
    )

    text_color_layer[:] = (
        120,
        235,
        0
    )

    result = cv2.bitwise_and(
        text_color_layer,
        text_color_layer,
        mask=mask
    )

    return result


# ==========================================
# 6. كلمات الأغنية
# ==========================================
#
# التوقيت:
#
# الجملة 1 : 3  - 8
# الجملة 2 : 9  - 15
# الجملة 3 : 16 - 21
# الجملة 4 : 22 - 27
# الجملة 5 : 28 - 34
# الجملة 6 : 35 - 40
# الجملة 7 : 41 - 42
# الجملة 8 : 42 - 44
# الجملة 9 : 45 - 48
#
# ==========================================

lyrics = [

    {
        "start": 3.0,
        "end": 8.0,
        "text": "روحي وما ملكت يداي فداه"
    },

    {
        "start": 9.0,
        "end": 15.0,
        "text": "وطني الحبيب وهل أحب سواهُ"
    },

    {
        "start": 16.0,
        "end": 21.0,
        "text": "وطني الذي قد عشت تحت سمائهِ"
    },

    {
        "start": 22.0,
        "end": 27.0,
        "text": "وهو الذي قد عشت فوق ثراهُ"
    },

    {
        "start": 28.0,
        "end": 34.0,
        "text": "منذ الطفولة قد عشقت ربوعه"
    },

    {
        "start": 35.0,
        "end": 40.0,
        "text": "إني أحب سهوله ورباهُ"
    },

    {
        "start": 41.0,
        "end": 42.0,
        "text": "وطني الحبيب"
    },

    {
        "start": 42.0,
        "end": 44.0,
        "text": "وطني الحبيب"
    },

    {
        "start": 45.0,
        "end": 48.0,
        "text": "وهل احب سواهُ ؟"
    }
]


# ==========================================
# 7. معرفة الجملة الحالية
# ==========================================

def get_current_lyric(elapsed):

    for lyric in lyrics:

        if (
            elapsed >= lyric["start"]
            and elapsed < lyric["end"]
        ):

            return lyric["text"], lyric["start"]

    # لا توجد جملة حاليًا
    return "", None


# ==========================================
# 8. إضافة الكلمات إلى الإطار
# ==========================================

def add_lyrics_to_frame(
    frame,
    elapsed
):

    current_text, current_timestamp = (
        get_current_lyric(elapsed)
    )

    # ======================================
    # إذا ما فيه جملة حاليًا
    # الشاشة تبقى بدون كلام
    # ======================================

    if current_text == "":
        return frame


    text_layer = create_arabic_text_image(
        current_text
    )


    # ======================================
    # ظهور تدريجي بسيط
    # ======================================

    text_progress = (
        elapsed - current_timestamp
    )

    alpha = min(
        1.0,
        max(
            0.0,
            text_progress / 0.35
        )
    )


    return cv2.addWeighted(
        frame,
        1.0,
        text_layer,
        alpha,
        0
    )


# ==========================================
# 9. الرسم الأصلي
# ==========================================

def draw_image_and_text_simultaneously(
    img_path="national_image.jpg",
    target_duration=12.0
):

    img = cv2.imread(
        img_path
    )

    if img is None:

        print(
            f"[-] تعذر العثور على الصورة "
            f"({img_path})."
        )

        return None


    # ======================================
    # تجهيز الصورة وتصغيرها
    # ======================================

    h_orig, w_orig = img.shape[:2]

    max_dim = 320

    scale = max_dim / float(
        max(
            h_orig,
            w_orig
        )
    )

    new_w = int(
        w_orig * scale
    )

    new_h = int(
        h_orig * scale
    )

    img_resized = cv2.resize(
        img,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA
    )


    # ======================================
    # تقليل الألوان
    # ======================================

    num_colors = 12

    data = img_resized.reshape(
        (-1, 3)
    ).astype(
        np.float32
    )

    criteria = (
        cv2.TERM_CRITERIA_EPS
        + cv2.TERM_CRITERIA_MAX_ITER,
        20,
        0.8
    )

    _, labels, centers = cv2.kmeans(
        data,
        num_colors,
        None,
        criteria,
        10,
        cv2.KMEANS_RANDOM_CENTERS
    )

    centers = np.uint8(
        centers
    )

    labels_grid = labels.reshape(
        (new_h, new_w)
    )


    # ======================================
    # التكبير لكامل الشاشة
    # ======================================

    scale_x = WIDTH / float(
        new_w
    )

    scale_y = HEIGHT / float(
        new_h
    )


    canvas = np.zeros(
        (HEIGHT, WIDTH, 3),
        dtype=np.uint8
    )


    cv2.namedWindow(
        WINDOW_NAME,
        cv2.WINDOW_NORMAL
    )


    # ======================================
    # استخراج مسارات الرسم
    # ======================================

    brightness = [
        np.mean(c)
        for c in centers
    ]

    sorted_color_indices = np.argsort(
        brightness
    )


    valid_contours_list = []


    for color_idx in sorted_color_indices:

        color_bgr = [
            int(c)
            for c in centers[color_idx]
        ]

        # استبعاد الخلفية البيضاء
        if sum(color_bgr) > 620:
            continue


        mask = (
            labels_grid == color_idx
        ).astype(
            np.uint8
        ) * 255


        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE
        )


        for contour in contours:

            if len(contour) >= 1:

                scaled_contour = (
                    contour.astype(
                        np.float32
                    )
                )


                scaled_contour[
                    :, 0, 0
                ] *= scale_x


                scaled_contour[
                    :, 0, 1
                ] *= scale_y


                scaled_contour = (
                    scaled_contour.astype(
                        np.int32
                    )
                )


                valid_contours_list.append(
                    (
                        scaled_contour,
                        color_bgr
                    )
                )


    total_items = len(
        valid_contours_list
    )


    if total_items == 0:
        return canvas


    print(
        "[+] بدء الرسم خلال "
        f"{target_duration} ثانية..."
    )


    start_time = time.time()

    current_idx = 0


    # ======================================
    # حلقة الرسم
    # ======================================

    while current_idx < total_items:

        elapsed = (
            time.time()
            - start_time
        )


        if elapsed >= target_duration:

            for idx in range(
                current_idx,
                total_items
            ):

                contour, color = (
                    valid_contours_list[idx]
                )


                cv2.drawContours(
                    canvas,
                    [contour],
                    -1,
                    color,
                    -1
                )


                cv2.drawContours(
                    canvas,
                    [contour],
                    -1,
                    color,
                    1
                )


            current_idx = total_items

            break


        target_progress = min(
            1.0,
            elapsed / target_duration
        )


        target_idx = int(
            target_progress * total_items
        )


        while (
            current_idx <= target_idx
            and current_idx < total_items
        ):

            contour, color = (
                valid_contours_list[
                    current_idx
                ]
            )


            cv2.drawContours(
                canvas,
                [contour],
                -1,
                color,
                -1
            )


            cv2.drawContours(
                canvas,
                [contour],
                -1,
                color,
                1
            )


            current_idx += 1


        combined_frame = (
            add_lyrics_to_frame(
                canvas.copy(),
                elapsed
            )
        )


        cv2.imshow(
            WINDOW_NAME,
            combined_frame
        )


        if (
            cv2.waitKey(1) & 0xFF
        ) == 27:

            return canvas


    # ======================================
    # انتظار حتى نهاية الـ 12 ثانية
    # ======================================

    while (
        time.time() - start_time
    ) < target_duration:

        elapsed = (
            time.time()
            - start_time
        )


        final_frame = (
            add_lyrics_to_frame(
                canvas.copy(),
                elapsed
            )
        )


        cv2.imshow(
            WINDOW_NAME,
            final_frame
        )


        if (
            cv2.waitKey(1) & 0xFF
        ) == 27:

            break


    print(
        "[✔] اكتمل الرسم بنجاح في "
        f"{time.time() - start_time:.2f} ثانية!"
    )


    return canvas


# ==========================================
# 10. إنشاء قناع للعلم فقط
# ==========================================

def create_flag_mask(image):

    mask = np.zeros(
        image.shape[:2],
        dtype=np.uint8
    )


    x1 = FLAG_X
    y1 = FLAG_Y


    x2 = min(
        WIDTH,
        FLAG_X + FLAG_W
    )


    y2 = min(
        HEIGHT - 130,
        FLAG_Y + FLAG_H
    )


    region = image[
        y1:y2,
        x1:x2
    ]


    if region.size == 0:
        return mask


    # ======================================
    # البحث عن اللون الأخضر السعودي
    # ======================================

    hsv = cv2.cvtColor(
        region,
        cv2.COLOR_BGR2HSV
    )


    lower_green = np.array([
        30,
        45,
        25
    ])


    upper_green = np.array([
        95,
        255,
        255
    ])


    green_mask = cv2.inRange(
        hsv,
        lower_green,
        upper_green
    )


    # ======================================
    # تنظيف القناع
    # ======================================

    kernel = np.ones(
        (7, 7),
        np.uint8
    )


    green_mask = cv2.morphologyEx(
        green_mask,
        cv2.MORPH_CLOSE,
        kernel
    )


    green_mask = cv2.morphologyEx(
        green_mask,
        cv2.MORPH_OPEN,
        kernel
    )


    # توسيع بسيط
    green_mask = cv2.dilate(
        green_mask,
        np.ones(
            (9, 9),
            np.uint8
        ),
        iterations=1
    )


    mask[
        y1:y2,
        x1:x2
    ] = green_mask


    return mask


# ==========================================
# 11. تحريك العلم فقط
# ==========================================

def animate_flag_only(
    completed_image
):

    print(
        "[+] بدأ تحريك العلم "
        "حتى نهاية العرض..."
    )


    original = (
        completed_image.copy()
    )


    flag_mask = (
        create_flag_mask(
            original
        )
    )


    start_time = time.time()


    while True:

        elapsed = (
            time.time()
            - start_time
        )


        if elapsed >= FLAG_DURATION:
            break


        progress = (
            elapsed
            / FLAG_DURATION
        )


        frame = (
            original.copy()
        )


        x1 = FLAG_X
        y1 = FLAG_Y


        x2 = min(
            WIDTH,
            FLAG_X + FLAG_W
        )


        y2 = min(
            HEIGHT - 130,
            FLAG_Y + FLAG_H
        )


        region = original[
            y1:y2,
            x1:x2
        ].copy()


        region_mask = flag_mask[
            y1:y2,
            x1:x2
        ]


        h, w = region.shape[:2]


        if h == 0 or w == 0:
            break


        # ==================================
        # موجة العلم
        # ==================================

        map_x = np.zeros(
            (h, w),
            dtype=np.float32
        )


        map_y = np.zeros(
            (h, w),
            dtype=np.float32
        )


        for yy in range(h):

            wave = (
                np.sin(
                    (
                        yy
                        / max(
                            1,
                            h
                        )
                    )
                    * np.pi
                    * 2
                    +
                    progress
                    * np.pi
                    * 4
                )
                * 10
            )


            for xx in range(w):

                map_x[
                    yy,
                    xx
                ] = np.clip(
                    xx + wave,
                    0,
                    w - 1
                )


                map_y[
                    yy,
                    xx
                ] = yy


        moving_region = cv2.remap(
            region,
            map_x,
            map_y,
            cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT
        )


        # ==================================
        # وضع بكسلات العلم
        # ==================================

        mask_bool = (
            region_mask > 0
        )


        destination = frame[
            y1:y2,
            x1:x2
        ]


        destination[
            mask_bool
        ] = moving_region[
            mask_bool
        ]


        frame[
            y1:y2,
            x1:x2
        ] = destination


        # ==================================
        # الكلمات تستمر أثناء حركة العلم
        # ==================================

        total_elapsed = (
            DRAW_DURATION
            + elapsed
        )


        frame = (
            add_lyrics_to_frame(
                frame,
                total_elapsed
            )
        )


        cv2.imshow(
            WINDOW_NAME,
            frame
        )


        if (
            cv2.waitKey(1) & 0xFF
        ) == 27:

            break


    cv2.imshow(
        WINDOW_NAME,
        original
    )


    cv2.waitKey(1)


    print(
        "[✔] انتهت حركة العلم."
    )


    return original


# ==========================================
# 12. استمرار عرض الكلمات بعد العلم
# ==========================================

def continue_lyrics(
    completed_image,
    start_elapsed
):

    print(
        "[+] استمرار عرض الكلمات..."
    )


    start_time = time.time()


    while True:

        elapsed_after_flag = (
            time.time()
            - start_time
        )


        total_elapsed = (
            start_elapsed
            + elapsed_after_flag
        )


        # انتهاء الكلمات
        if total_elapsed >= LYRICS_END:

            final_frame = (
                completed_image.copy()
            )


            cv2.imshow(
                WINDOW_NAME,
                final_frame
            )


            cv2.waitKey(1)

            break


        frame = (
            completed_image.copy()
        )


        frame = (
            add_lyrics_to_frame(
                frame,
                total_elapsed
            )
        )


        cv2.imshow(
            WINDOW_NAME,
            frame
        )


        if (
            cv2.waitKey(1) & 0xFF
        ) == 27:

            break


    print(
        "[✔] انتهت جميع الكلمات."
    )


# ==========================================
# 13. التشغيل الرئيسي
# ==========================================

def main():

    print(
        "------------------------------------------"
    )


    print(
        "بدء العرض الوطني"
    )


    print(
        "الرسم: 12 ثانية"
    )


    print(
        "حركة العلم: حتى نهاية العرض"
    )


    print(
        "الكلمات حتى: 48 ثانية"
    )


    print(
        "------------------------------------------"
    )


    # ======================================
    # Arduino يبدأ أولاً
    # ======================================

    send_signal_to_arduino(
        COM_PORT
    )


    # ======================================
    # الرسم
    # ======================================

    completed_image = (
        draw_image_and_text_simultaneously(
            img_path="national_image.jpg",
            target_duration=DRAW_DURATION
        )
    )


    if completed_image is None:

        cv2.destroyAllWindows()

        return


    # ======================================
    # حركة العلم
    # ======================================

    animate_flag_only(
        completed_image
    )


    # ======================================
    # بعد الرسم + حركة العلم
    #
    # مرّ 48 ثانية
    # ======================================

    continue_lyrics(
        completed_image,
        DRAW_DURATION + FLAG_DURATION
    )


    # ======================================
    # النهاية
    # ======================================

    black = np.zeros(
        (HEIGHT, WIDTH, 3),
        dtype=np.uint8
    )


    cv2.imshow(
        WINDOW_NAME,
        black
    )


    cv2.waitKey(1000)


    cv2.destroyAllWindows()


    print(
        "------------------------------------------"
    )


    print(
        "[✔] انتهى العرض كاملًا."
    )


    print(
        "------------------------------------------"
    )


# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    main()
