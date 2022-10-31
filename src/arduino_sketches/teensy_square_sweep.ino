/*
  led square flicker sweep for teensy
 */

const int num_freq = 18;
// frequencies in Hz
const float freq[num_freq] {1.0, // 0
                    2.0, // 1
                    4.0, // 2
                    8.0, // 3
                    16.0, // 4
                    32.0, // 5
                    64.0, // 6
                    127.99, // 7
                    256.02, // 8
                    512.03, // 9
                    1023.54, // 10
                    2049.18, // 11
                    4098.36, // 12
                    8196.72, // 13
                    16393.44, // 14
                    32258.06, // 15
                    66666.67, // 16
                    125000 // 17
                    }; 
const int led_pin = 23;

// --- non-const
unsigned long int first_half_period_usec[num_freq];
unsigned long int second_half_period_usec[num_freq];
unsigned long t_last;
bool is_on;
const float duty_cycle = 0.5;
void setup() {
  Serial.begin(9600);

  pinMode(led_pin, OUTPUT);
  for (int i = 0; i < num_freq; i++) {
    first_half_period_usec[i] = round(duty_cycle * 1.0e6 / freq[i]);
    second_half_period_usec[i] = round(1.0e6 /freq[i]) - first_half_period_usec[i];
    Serial.print("frequency[");
    Serial.print(i);
    Serial.print("] = ");
    Serial.println(1000000.0 / (first_half_period_usec[i] + second_half_period_usec[i]));
  }
  t_last = micros();
  is_on = false;
}

void run_frequency(int f_idx, int num_half_periods) {
   Serial.print("frequency: ");
   Serial.println(1000000.0 / (first_half_period_usec[f_idx] + second_half_period_usec[f_idx])); 
   int half_period_cnt = 0;
   while (half_period_cnt < num_half_periods) {
    const unsigned long t_clock = micros();
    // modular arithmetic should automatically handle the case when
    // t_clock has wrapped around such that t_last > t_clock
    const unsigned long dt = t_clock - t_last;  
    if ((is_on && dt >= first_half_period_usec[f_idx])
        || (!is_on && dt >= second_half_period_usec[f_idx])) {
        digitalWrite(led_pin, is_on ? LOW : HIGH);
      is_on = !is_on;
      t_last = t_clock;
      half_period_cnt++;
      }
   }
}

// linear frequency sweep
void loop() {
  const int num_half_periods = 20;

  for (int f_idx = 0; f_idx < num_freq; f_idx++) {
    run_frequency(f_idx, num_half_periods);
  }
  for (int f_idx = num_freq - 1; f_idx >=  0; f_idx--) {
    run_frequency(f_idx, num_half_periods);
  }
}

// random frequency sweep
void loop_random() {
  const int num_half_periods = 20;
  const int num_samples = 100;
  for (int i = 0; i < num_samples; i++) {
    const int f_idx = random(0, num_freq);
    run_frequency(f_idx, num_half_periods);
  }
}
