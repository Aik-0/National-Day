// ==========================================
// NATIONAL SHOW - ARDUINO (وطني الحبيب - 48 ثانية)
// ==========================================

const int leds[] = {2, 3, 4, 5, 6};
const int LED_COUNT = 5;

const int buzzer = 8;

// ==========================================
// نغمات اللحن الكامل الموزعة على 48 ثانية
// ==========================================
// النغمات (الترددات بالـ Hz) مع السكتات (0)
int melody[] = {
  // المقطع الأول (المقدمة)
  392, 440, 494, 523, 587, 523, 494, 440, 0,
  392, 440, 494, 523, 587, 659, 587, 523, 0,
  587, 659, 698, 659, 587, 523, 494, 440, 392, 0,
  
  // المقطع الثاني (تكرار المعزوفة وتطوير اللحن)
  392, 440, 494, 523, 587, 523, 494, 440, 0,
  392, 440, 494, 523, 587, 659, 587, 523, 0,
  587, 659, 698, 659, 587, 523, 494, 440, 392, 0,

  // المقطع الثالث (الختام والإيقاع الممتد)
  523, 587, 659, 698, 784, 698, 659, 587, 0,
  523, 587, 659, 587, 523, 494, 440, 392, 0
};

// مدة كل نغمة بالميللي ثانية موزونة لتغطي الـ 48 ثانية
int noteDurations[] = {
  // المقطع الأول
  400, 400, 400, 600, 400, 400, 400, 800, 300,
  400, 400, 400, 600, 400, 400, 400, 800, 300,
  400, 400, 400, 600, 400, 400, 400, 400, 1000, 400,

  // المقطع الثاني
  400, 400, 400, 600, 400, 400, 400, 800, 300,
  400, 400, 400, 600, 400, 400, 400, 800, 300,
  400, 400, 400, 600, 400, 400, 400, 400, 1000, 400,

  // المقطع الثالث
  450, 450, 450, 650, 450, 450, 450, 900, 400,
  450, 450, 450, 650, 450, 450, 450, 1200, 500
};

const int MELODY_COUNT = sizeof(melody) / sizeof(melody[0]);

// ==========================================

bool showRunning = false;

unsigned long showStartTime = 0;
unsigned long lastBeatTime = 0;

int currentNote = 0;
int currentNoteDuration = 250; 

// ==========================================

void setup() {
  Serial.begin(9600);

  pinMode(buzzer, OUTPUT);

  for (int i = 0; i < LED_COUNT; i++) {
    pinMode(leds[i], OUTPUT);
    digitalWrite(leds[i], LOW);
  }

  noTone(buzzer);
}

// ==========================================

void stopEverything() {
  noTone(buzzer);

  for (int i = 0; i < LED_COUNT; i++) {
    digitalWrite(leds[i], LOW);
  }

  showRunning = false;
}

// ==========================================

void startShow() {
  showRunning = true;
  showStartTime = millis();
  lastBeatTime = 0;
  currentNote = 0;
  currentNoteDuration = 0;
}

// ==========================================

void playBeat() {
  // إطفاء الليدات
  for (int i = 0; i < LED_COUNT; i++) {
    digitalWrite(leds[i], LOW);
  }

  // تشغيل النغمة أو إيقافها عند السكتة (0)
  if (melody[currentNote] == 0) {
    noTone(buzzer);
  } else {
    // تشغيل الليد التتابعي
    int ledNumber = currentNote % LED_COUNT;
    digitalWrite(leds[ledNumber], HIGH);
    
    // تشغيل الصوت
    tone(buzzer, melody[currentNote]);
  }

  // تحديد مدة النغمة الحالية
  currentNoteDuration = noteDurations[currentNote];

  currentNote++;

  if (currentNote >= MELODY_COUNT) {
    currentNote = 0; // إعادة اللحن تلقائياً عند انتهائه قبل مدة العرض
  }
}

// ==========================================

void loop() {

  // استقبال أوامر Python
  if (Serial.available()) {
    char command = Serial.read();

    if (command == '1') {
      startShow();
    }

    if (command == '0') {
      stopEverything();
    }
  }

  if (!showRunning) {
    return;
  }

  unsigned long now = millis();

  // إيقاف العرض تماماً بعد 48 ثانية (48000 مللي ثانية)
  if (now - showStartTime >= 48000) {
    stopEverything();

    // تأثير الفلاش النهائي عند اكتمال الـ 48 ثانية
    for (int j = 0; j < 3; j++) {
      for (int i = 0; i < LED_COUNT; i++) {
        digitalWrite(leds[i], HIGH);
      }
      delay(150);

      for (int i = 0; i < LED_COUNT; i++) {
        digitalWrite(leds[i], LOW);
      }
      delay(150);
    }
    return;
  }

  // الانتقال للنغمة التالية بناءً على زمن النغمة الحالية
  if (now - lastBeatTime >= currentNoteDuration) {
    lastBeatTime = now;
    playBeat();
  }
}