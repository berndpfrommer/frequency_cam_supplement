# Supplemental code and data to reproduce images in FrequencyCam paper


## How to make the videos

### Guitar video

Create frames and extract audio from bag:
```
rm -rf frames
ros2 launch launch/guitar.launch.py bag:=./data/guitar
python3 src/bag_audio2wav.py  ./data/guitar
```
Glue everything together using ``ffmpeg``:
```
ffmpeg -framerate 25 -pattern_type glob -i 'frames/*.jpg'   -c:v libx264 -pix_fmt yuv420p out.mp4
ffmpeg -i out.mp4 -i audio.wav -map 0:v -map 1:a -c:v copy -shortest guitar.mp4
```

### Quad rotor video

Create frames:
```
rm -rf frames
ros2 launch launch/quad_rotor.launch.py bag:=./data/quad_rotor
rm frames/frame_000[0-3]*
rm frames/frame_0004[0-8]*
```
Use ffmpeg to glue together:
```
ffmpeg -framerate 100 -pattern_type glob -i 'frames/*.jpg'   -c:v libx264 -pix_fmt yuv420p quad_rotor.mp4
```

# How to reproduce graphs

## Curve plots
To get the final graph you need to detach the window (shift-alt-space in i3wm)
and pull it to the right size.
```
# fig:baseline
python3 ./src/baseline.py  --bag ./data/single_pixel/square_wave_50hz -p 153279 -n 130 -s 130

# fig:simple_detrend
python3 ./src/plot_filter.py --bag ./data/single_pixel/wiggle_100hz -0 -p 153279 --skip 20 -n 300

# fig:transfer_functions
python3 ./src/plot_filter.py --cutoff_period 10

# fig:filter_examples
python3 ./src/plot_filter.py  --bag ./data/single_pixel/wiggle_100hz -0 -p 153279 --filter --cutoff_period 144 -n 300 -s 40

# fig:reconstruction_square_triangle
python3 ./src/reconstruction_baseline_vs_filter.py -p 153279 --config_file ./src/reconstruction_baseline_vs_filter.yaml

# fig:dark_noise
python3 ./src/plot_darknoise_filter.py  --bag ./data/single_pixel/frequency_sweep -0 -p 153279 --filter_pass_dt 15e-6 --filter_dead_dt 15e-6 --skip 245 -n 50

# fig:dark_noise_filtered
python3 ./src/plot_darknoise_filter.py  --bag ./data/single_pixel/frequency_sweep -0 -p 153279 --filter_pass_dt 15e-6 --filter_dead_dt 15e-6 --show_filtered --skip 245 -n 500

# fig:square_wave
python3 ./src/baseline_vs_filter.py  -p 153279 --config=./src/baseline_vs_filter_square.yaml

# fig:triangle_wave
python3 ./src/baseline_vs_filter.py  -p 153279 --config=./src/baseline_vs_filter_triangle.yaml

# fig:frequency_sweep_overview
python3 ./src/reconstruction_sweep.py -p 153279 --filter_pass_dt 15e-6 --config_file ./src/reconstruction_sweep.yaml

# fig:frequency_sweep_detail  (must pan and zoom afterwards)
python3 ./src/reconstruction_sweep.py -p 153279 --filter_pass_dt 15e-6 --config_file ./src/reconstruction_sweep.yaml --no-warp

# fig:roi_reconstruction
python3 ./src/roi_scaling_plot.py -p 153279 --config_file ./src/roi_scaling_recon.yaml --show_reconstruction --filter_pass_dt 15e-6 --filter_dead_dt 15e-6

# fig:roi_freq
python3 ./src/roi_scaling_plot.py -p 153279 --config_file ./src/roi_scaling_freq.yaml  --filter_pass_dt 15e-6 --filter_dead_dt 15e-6
```

# Frequency images

```
# fig:quad_freq
python3 ../frequency_cam/src/mv_vs_frequency_cam.py -b ./data/quad_rotor --freq_min 220 --freq_max 300 --tlx 0 --tly 160 --brx 242 --bry 441 -l 220 240 260 280 300 --scale 5.0 --font_scale 5.0 --font_thickness 10
# then grab frame 00753

# fig:leds_freq
python3 ../frequency_cam/src/mv_vs_frequency_cam.py -b ./data/leds_16_4096 --freq_min 10.0 --freq_max 5000.0 --log_scale --font_scale 7.0 --font_thickness 15 --text_height 40 --cutoff_period 5 --scale 5 -l 16 32 64 128 256 512 1024 2048 4096 --debug_x 306 --debug_y 152 --scale 5
# then grab frame 7

# fig:guitar_freq
python3 ../frequency_cam/src/mv_vs_frequency_cam.py -b ./data/guitar --freq_min 70 --freq_max 300 -l 73.4 110.0 146.8 185.0 220.0 293.7 --font_scale 10.0 --font_thickness 20 --scale 5.0 --text_height 50
% then pick frame 577
```

## Random notes

### Quad rotor
From manually analyzing the frames the time of one rotation is about
8ms or 7500rpm. This corresponds to (two blades!) a flicker frequency
of about  250Hz. Used was SilkyEVCam #1 (#0293) with metavision 2.2
and the following bias settings
```
299  % bias_diff
221  % bias_diff_off
384  % bias_diff_on
1399 % bias_fo
1250 % bias_hpf
1250 % bias_pr
1500 % bias_refr
```
Note: could not reproduce those with MV 2.3


### Frequency sweep
Used bias settings of ``bias_fo=1250`` after also trying 1299, 1346,
and 1399.
