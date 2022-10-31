/*
  led ramp up/down with wiggle for the teensy 4.1
 */

const float freq = 1.0; // cycles per second
const int NUM_STEPS = 50; // number of steps for half cycle
const int NUM_STEPS_1 = 20; // num steps up before first decline
const int NUM_STEPS_2 = 40; // num steps before final ascent

// 2 * NUM_STEPS * freq must factor 1e6 = 2^6 * 5^6.
// meaning NUM_STEPS and freq combined can have at most 5 times
// the factor of 2 and 6 times the factor of 5, and must have
// no other prime factors

const int resolution = 10; // number of bits signal resolution

const bool repeat_peaks = false; // setting this to true will mess up frequency!

const int num_samples_per_cycle = 2 * NUM_STEPS + (repeat_peaks ? 1 : 0);
const unsigned long sample_time_usec = (unsigned long)(1.0e6 / (num_samples_per_cycle * freq));
const float true_freq = 1.0 / (1e-6 * (num_samples_per_cycle * sample_time_usec));

const int max_level_max = (1 << resolution);


// experimentally determined minimum values for LED to switch on,
// for different resolutions
// below this value the light goes completely dark
const int min_level_min[16] = {
  0, // place holder
  0, // place holder
  3, // 2 bits
  4, // 3 bits
  4, // 4 bits
  4, // 5 bits
  4, // 6 bits
  4, // 7 bits
  4, // 8 bits
  4, // 9 bits (only 1 LED lit)
  5, // 10 bits
  5, // 11 bits
  5, // 12 bits
  5, // 13 bits
  5, // 14 bits
  5  // 15 bits
};

// the minimum level must be set depending on resolution,
// then tweaked up a little because the lower end is no longer
// accurately linear
const int min_level = int(min_level_min[resolution] * 1.2); // 1.2 worked
// The upper end of the range also gives more events than expected
const int max_level = int(max_level_max * 0.95); // 0.95 worked
const float mid_level = 0.5 * (min_level + max_level);

// table of optimal frequencies for the teensy 4.1 (600MHz CPU):

const float optimal_frequency[16] = {
  0, // place holder
  75000000,  // place holder
  37500000,  // 2 bits
  18750000,  // 3 bits
  9375000,   // 4 bits
  4687500,   // 5 bits
  2343750,   // 6 bits 
  1171875.0, // 7 bits
  585937.50, // 8 bits
  292968.75, // 9 bits
  146484.38, // 10 bits
  73242.19,  // 11 bits
  36621.09,  // 12 bits
  18310.55,  // 13 bits
  9155.27,   // 14 bits
  4577.64    // 15 bits
};


unsigned long t_last;
const int led_pin = 23;


void setup() {
  Serial.begin(9600);
  const float f = optimal_frequency[resolution];
  
  //Declaring LED pin as output
  pinMode(led_pin, OUTPUT);
  
  analogWriteResolution(resolution);
  // this sets the frequency for all pins driven
  // by the same clock
  analogWriteFrequency(led_pin, f);

  Serial.print("true freq: ");
  Serial.println(true_freq);
  Serial.print("resolution: ");
  Serial.println(resolution);
  Serial.print("sample time [usec]: ");
  Serial.println(sample_time_usec);
  Serial.print("min level: ");
  Serial.println(min_level);
  Serial.print("max level: ");
  Serial.println(max_level);
  Serial.print("pwm frequency:");
  Serial.println(f);


  /*
  const long cpu_freq = F_CPU * 1e-6;
  Serial.print("cpu frequency:");
  Serial.println(cpu_freq);
  */
  analogWrite(led_pin, 0);  
  t_last = micros();
}


uint64_t t_usec = 0; // elapsed time in microseconds
int counter = 0;
int section = 0;


float level = min_level;

float fac = pow(float(max_level) / float(min_level), 1.0 / NUM_STEPS_1);

// the loop routine runs over and over again forever:
void loop() {
  
  const unsigned long t_clock = micros();
  const unsigned long dt = t_clock - t_last;

  if (dt >= sample_time_usec) {
    t_usec += dt;
    //const float level = min_level * pow(base, float(counter));    
    analogWrite(led_pin, round(level));
    //analogWrite(led_pin, round(0.5 * max_level));
    Serial.print(counter);
    Serial.print(" ");
    Serial.println(level);
    switch (section) {
      case 0:
      if (counter >= NUM_STEPS_1) {
        section = 1;
        fac = 1.0 / pow(float(max_level) / mid_level,
                        1.0 / (NUM_STEPS_2 - NUM_STEPS_1)); 
      } break;
      case 1:
      if (counter >= NUM_STEPS_2) {
        section = 2;
        fac = pow(float(max_level) / mid_level,
                          1.0 / (NUM_STEPS - NUM_STEPS_2)); 
      } break;
      case 2:
      if (counter >= NUM_STEPS) {
        section = 3;
        fac = 1.0 / pow(float(max_level) / mid_level,
                          1.0 / (NUM_STEPS_1));
      } break;
      case 3:
      if (counter >= NUM_STEPS + NUM_STEPS_1) {
        section = 4;
        fac = pow(float(max_level) / mid_level,
                        1.0 / (NUM_STEPS_2 - NUM_STEPS_1));
      } break;
      case 4:
      if (counter >= NUM_STEPS + NUM_STEPS_2) {
        section = 5;
        fac = 1.0 / pow(float(max_level) / min_level,
                        1.0 / (NUM_STEPS - NUM_STEPS_2));
      } break;
      case 5:
      if (counter >= 2 * NUM_STEPS) {
        section = 0;
        fac = pow(float(max_level) / float(min_level), 1.0 / NUM_STEPS_1);
        level = min_level; // make sure to restart always from same point
        counter = -1;
      } break;
    }
    level *= fac;
    counter++;

    t_last = t_clock;
  }
}
