/*
  led square flicker for teensy using multiple LEDs
 */

const int num_leds = 9;
// frequency in hz
const float freq[num_leds] = { 8, 16,  32, 64, 256, 512,  1024, 2048, 4096};
const int first_led_pin = 0;
int led_pin[num_leds];

// --- non-const
unsigned long int half_period_usec[num_leds];
unsigned long t_last[num_leds];
bool is_on[num_leds];

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < num_leds; i++) {
    led_pin[i] = first_led_pin + i;
    pinMode(led_pin[i], OUTPUT);
    half_period_usec[i] = round(0.5 * 1.0e6 / freq[i]);
    Serial.print("frequeny[");
    Serial.print(i);
    Serial.print("] = ");
    Serial.println(1000000 / (2 * half_period_usec[i]));
    t_last[i] = micros();
    is_on[i] = false;
  }
}

// the loop routine runs over and over again forever:
void loop() {
  const unsigned long t_clock = micros();

  for (int i = 0; i < num_leds; i++) {
    // modular arithmetic should automatically handle the case when
    // t_clock has wrapped around such that t_last > t_clock

    const unsigned long dt = t_clock - t_last[i];  
    if (dt >= half_period_usec[i]) {
      digitalWrite(led_pin[i], is_on[i] ? LOW : HIGH);
      is_on[i] = !is_on[i];
      t_last[i] = t_clock;
    }
  }
}
