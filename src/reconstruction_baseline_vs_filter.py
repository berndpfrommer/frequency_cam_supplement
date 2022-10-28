#!/usr/bin/python3
# -----------------------------------------------------------------------------
# Copyright 2022 Bernd Pfrommer <bernd.pfrommer@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#

import matplotlib.pyplot as plt
import argparse
import numpy as np
import read_bag_ros2
import yaml
import core_filtering


def read_yaml(filename):
    with open(filename, 'r') as y:
        try:
            return yaml.load(y)
        except yaml.YAMLError as e:
            print(e)


def draw_arrows(ax, tsc, t_start, t_end, all_t, label, level, fontsize, color):
    for too in all_t:
        if too[1] > t_start and too[0] < t_end:
            ax.annotate("", xy=((too[0] - t_start) * tsc, too[2]),
                        xytext=((too[1] - t_start) * tsc, too[2]),
                        arrowprops=dict(
                            arrowstyle="->, head_width=0.3, head_length=1.0",
                            lw=3.5, color=color))
            ax.text((0.75 * too[1] + 0.25 * too[0] - t_start) * tsc,
                    too[2] + level, label, ha='center',
                    fontsize=fontsize, color=color)
            
def set_tick_font_size(ax, fs):
    """set_tick_font_size(): sets tick font sizes for x and y"""
    for tl in ax.get_xticklabels() + ax.get_yticklabels():
        tl.set_fontsize(fs)


def set_font_size(axs, fontsize):
    for ax in axs:
        ax.title.set_fontsize(fontsize)
        ax.yaxis.label.set_fontsize(fontsize)
        ax.xaxis.label.set_fontsize(fontsize)
        set_tick_font_size(ax, fontsize)


def find_periods_baseline(data, L, T):
    last_t = [None, None]
    last_p = None
    period = [[], []]
    times = [[], []]
    cnt = int(0)
    period_omit = 2 * int(round(T))
    for i, d in enumerate(data):
        t = d[0]
        p = d[1]
        if last_p is not None and last_p != p:
            if p:
                if last_t[0] is not None and cnt > period_omit:
                    period[0].append(t - last_t[0])
                    times[0].append((t, last_t[0], 1e9 * L[i]))
                last_t[0] = t
            else:
                if last_t[1] is not None and cnt > period_omit:
                    period[1].append(t - last_t[1])
                    times[1].append((t, last_t[1], 1e9 * L[i]))
                last_t[1] = t
        last_p = p
        cnt += 1
    return 1e-9 * np.array(times[0]), 1e-9 * np.array(period[0]), \
        1e-9 * np.array(times[1]), 1e-9 * np.array(period[1])


def reconstruct(data, T):
    alpha = core_filtering.compute_alpha_for_cutoff(T)
    beta  = core_filtering.compute_beta_for_cutoff(T)
    dL = np.where(data[:, 1] == 0, -1, 1)
    return  core_filtering.filter_iir(dL, alpha, beta, (0, 0))


def find_periods_filtered(data, L_all, T):
    t_all = data[:, 0]

    # drop the first 2 * cutoff period
    period_omit = 2 * int(round(T))
    t_prev, L_prev = None, None
    t_flip, t_flip_interp = [], []
    dt, dt_interp = [], []
    upper_half = False
    cnt = 0
    for t, L in zip(t_all, L_all):
        if upper_half and L < 0:
            if cnt > period_omit:
                # regular periods
                if t_flip: # has element
                    dt.append(t - t_flip[-1][0])
                    t_flip.append((t, t_flip[-1][0], L * 1e9))
                else:
                    t_flip.append((t, t, L * 1e9))
                # ------ interpolated periods
                if L_prev:
                    dt_int = t - t_prev
                    dL_int = L - L_prev
                    t_interp = t_prev - dt_int * L_prev / dL_int
                    if t_flip_interp:
                        dt_interp.append(t_interp - t_flip_interp[-1][0])
                        t_flip_interp.append((t_interp, t_flip_interp[-1][0], 0))
                    else:
                        t_flip_interp.append((t_interp, t_interp, 0))
        upper_half = L > 0
        t_prev = t  # for interpolation
        L_prev = L  # for interpolation
        cnt += 1

    return (1e-9 * np.array(t_flip), 1e-9 * np.array(dt),
            1e-9 * np.array(t_flip_interp), 1e-9 * np.array(dt_interp)), t_all, L_all


def plot_periods(ax, args, times_and_periods_baseline,
                 times_and_periods_filtered, data, skip_plot, num_plot):
    """plot_pixel() plots pixel data"""

    # convert tuples to something more readable
    times_off_on, periods_off_on, times_on_off, periods_on_off = \
        times_and_periods_baseline
    t_filtered, periods_filtered, t_interp, periods_interp = \
        times_and_periods_filtered[0]
    t, L = times_and_periods_filtered[1:3]

    fontsize = 30
    # ---- histogram of periods
    tsc = 1e3
    t_sec = t * 1e-9
    s = skip_plot
    e = min(s + num_plot, t.shape[0])
    ax.plot((t_sec[s:e] - t_sec[s]) * tsc,
                L[s:e], 'o-', label=r'$\tilde{L}(t)$')
    ax.plot((t_sec[s:e] - t_sec[s]) * tsc, np.zeros(t_sec[s:e].shape[0]), '--',
            color='grey')
    draw_arrows(ax, tsc, t_sec[s], t_sec[e - 1], times_on_off, 'baseline',
                1.1, fontsize * 0.7, color='green')
    draw_arrows(ax, tsc, t_sec[s], t_sec[e - 1], t_filtered, 'filtered',
                -2.0, fontsize * 0.7, color='red')
    draw_arrows(ax, tsc, t_sec[s], t_sec[e - 1], t_interp, 'interpolated',
                1.1, fontsize * 0.7, color='black')
    ax.set_ylabel(r'$\tilde{L}(t)$')
    # set font size for title, axis labels and ticks
    set_font_size((ax, ), fontsize)


def make_graph(ax, args, data, res, cutoff_period, skip_plot, num_plot):
    if args.filter_pass_dt > 0:
        data = core_filtering.filter_noise(
            data, args.filter_pass_dt, args.filter_dead_dt)
    L = reconstruct(data, cutoff_period)
    plot_periods(ax, args, find_periods_baseline(data, L, cutoff_period),
                 find_periods_filtered(data, L, cutoff_period), data,
                 skip_plot, num_plot)


def to_tuple(ax):
    try:
        _ = iter(ax)
        return ax   # already is tuple
    except TypeError:
        return (axs, )  # not a tuple make it 
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='show different reconstruction methods.')
    parser.add_argument('--topic', '-t', action='store', default='/event_camera/events',
                        required=False, help='ros topic')
    parser.add_argument('--pixel', '-p', action='store', default=None,
                        required=True, type=int,
                        help='which pixel to plot')
    parser.add_argument('--skip', action='store', default=0, type=int,
                        help='number of events to skip on read')
    parser.add_argument('--max_read', '-m', action='store', default=None,
                        required=False, type=int,
                        help='how many events to read (total)')
    parser.add_argument('--filter_pass_dt', action='store', default=0e-6,
                        type=float, help='passing dt between OFF followed by ON')
    parser.add_argument('--filter_dead_dt', action='store',
                        default=None, type=float,
                        help='filter dt between event preceeding OFF/ON pair')
    parser.add_argument('--config_file', action='store', default=None,
                        required=True, help='name of yaml file with config')

    args = parser.parse_args()
    if args.filter_dead_dt is None:
        args.filter_dead_dt = args.filter_pass_dt

    cfg = read_yaml(args.config_file)
    fig, axs = plt.subplots(nrows=len(cfg['graphs']), ncols=1, sharex=True)
    axs = to_tuple(axs)
     
    for ax, c in zip(axs, cfg['graphs']):
        array, res = read_bag_ros2.read_as_array(
            bag_path=cfg['base_dir'] + '/' + c['bag'], topic=args.topic,
            use_sensor_time=True, skip=c['skip'],
            max_read=c['max_read'])
        make_graph(ax, args, array[args.pixel], res,
                   cutoff_period=c['cutoff_period'],
                   skip_plot=c['skip_events_plot'], num_plot=c['num_events_plot'])

    plt.subplots_adjust(left=0.15, right=0.98, top=0.98, bottom=0.1,
                        hspace=0.1, wspace=0.04)
    axs[-1].set_xlabel('time [ms]')

    plt.show()
