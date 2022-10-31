/*
  led square flicker for teensy
 */

const int num_leds = 1;
// frequency in hz
//const float freq[num_leds] = { 125000};
//const float freq[num_leds] = { 131072.0};
const float ff[18] {1.0, // 0
                    2.0, // 1
                    4.0, // 2
                    8.0, // 3
                    16.0, // 4
                    32.0, // 5
                    64.0, // 6
                    128.0, // 7
                    256.0, // 8
                    512.0, // 9
                    1024.0, // 10
                    2048.0, // 11
                    4096.0, // 12
                    8192.0, // 13
                    16384.0, // 14
                    32768.0, // 15
                    65536.0, // 16
                    131072.0}; // 17
const float freq[num_leds] = { ff[17]};
const int led_pin[num_leds] = {23};

// --- non-const
unsigned long int first_half_period_usec[num_leds];
unsigned long int second_half_period_usec[num_leds];
unsigned long t_last[num_leds];
bool is_on[num_leds];
const float duty_cycle = 0.5;
void setup() {
  Serial.begin(9600);

  for (int i = 0; i < num_leds; i++) {
    pinMode(led_pin[i], OUTPUT);
    first_half_period_usec[i] = round(duty_cycle * 1.0e6 / freq[i]);
    second_half_period_usec[i] = round(1.0e6 /freq[i]) - first_half_period_usec[i];
    Serial.print("frequency[");
    Serial.print(i);
    Serial.print("] = ");
    Serial.println(1000000.0 / (first_half_period_usec[i] + second_half_period_usec[i]));
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
    if ((is_on[i] && dt >= first_half_period_usec[i])
    || (!is_on[i] && dt >= second_half_period_usec[i])) {
      digitalWrite(led_pin[i], is_on[i] ? LOW : HIGH);
      is_on[i] = !is_on[i];
      t_last[i] = t_clock;
    }
  }
}
