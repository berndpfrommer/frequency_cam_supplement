/*
  led ramp up/down controller for the teensy 4.1
 */

const float freq = 2000.0; // cycles per second
const int NUM_STEPS = 50; // number of steps between max and min

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
const int led_pin = 2;


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
int dir = 1; // count upwards first

const float base = pow(float(max_level) / float(min_level), 1.0 / NUM_STEPS);
float level = min_level;
float fac = base;

// the loop routine runs over and over again forever:
void loop() {
  
  const unsigned long t_clock = micros();
  if (t_clock < t_last) { // handle overflow
     t_last = t_last + (1 << 31); // also overflow t_last
  }
  const unsigned long dt = t_clock - t_last;

  if (dt >= sample_time_usec) {
    t_usec += dt;
    //const float level = min_level * pow(base, float(counter));    
    analogWrite(led_pin, round(level));

    //Serial.print(t_usec);
    //Serial.print(" ");
    //Serial.println(level);
    counter += dir;
    level *= fac;
    if (counter > NUM_STEPS) {
      dir = -1;
      fac = 1.0 / base;
      counter = repeat_peaks ? NUM_STEPS : (NUM_STEPS - 1);
      level = max_level;
    } else if (counter < 0) {
      dir = 1;
      counter = repeat_peaks ? 0 : 1;
      level =  min_level;
      fac = base;
    }
   
    t_last = t_clock;
  }
}
