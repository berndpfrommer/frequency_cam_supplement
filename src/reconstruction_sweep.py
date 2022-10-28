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


freq_table = (1.0, # 0
              2.0, # 1
              4.0, # 2
              8.0, # 3
              16.0, # 4
              32.0, # 5
              64.0, # 6
              127.99, # 7
              256.02, # 8
              512.03, # 9
              1023.54, # 10
              2049.18, # 11
              4098.36, # 12
              8196.72, # 13
              16393.44, # 14
              32258.06, # 15
              66666.67, # 16
              125000, # 17
              )


def read_yaml(filename):
    with open(filename, 'r') as y:
        try:
            return yaml.load(y)
        except yaml.YAMLError as e:
            print(e)

            
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
    period_omit = -1
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
    return core_filtering.filter_iir(dL, alpha, beta, (0, 0))


def find_periods_filtered(data, L_all, T):
    t_all = data[:, 0]

    # HACK:
    # special initialization to capture the first period
    # of this particular dataset
    period_omit = -1
    t_prev, L_prev = t_all[0], 0
    upper_half = True  # set to upper half, just for this data set
    t_flip = [(t_prev, t_prev, 1e9*L_prev)]
    t_flip_interp = [(t_prev, t_prev, 1e9*L_prev)]
    dt, dt_interp = [], []
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
                        t_flip_interp.append(
                            (t_interp, t_flip_interp[-1][0], 0))
                    else:
                        t_flip_interp.append((t_interp, t_interp, 0))
        upper_half = L > 0
        t_prev = t  # for interpolation
        L_prev = L  # for interpolation
        cnt += 1
    # remove the first two elements as they are spurious
    del t_flip[0:2]
    del t_flip_interp[0:2]
    return (1e-9 * np.array(t_flip), 1e-9 * np.array(dt),
            1e-9 * np.array(t_flip_interp),
            1e-9 * np.array(dt_interp)), t_all, L_all


def dilate_time(t_all, t_start, do_dilate):
    dilated_time = []
    f_idx = 0
    step = 1
    num_cycles = 10
    t_last = t_start
    t_lim = t_last + num_cycles / freq_table[f_idx]
    slot_idx = 0
    tick_marks = []
    t_limits = [t_lim]
    for t in t_all:
        # if t crossed into next frequency epoch, find limits
        # of next epoch
        while t > t_lim:
            t_last = t_lim
            # if last or first frequency has been reached, reverse direction,
            # but don't change the frequency, because the frequency is
            # repeated once
            if (f_idx == len(freq_table) - 1 and step > 0) \
               or (f_idx == 0 and step < 0):
                step = -step
            else:  # frequency repeats?
                f_idx += step
            # print(f'freq {freq_table[f_idx]} starts at t: {t_lim}')
            slot_idx += 1
            tick_marks.append(t_lim - t_start)
            t_lim += num_cycles / freq_table[f_idx]
            t_limits.append(t_lim)
            if slot_idx == 2 * len(freq_table) - 1:
                break
        dilated_time.append(slot_idx +
                            (t - t_last) * freq_table[f_idx] / num_cycles)
        if slot_idx == 2 * len(freq_table) - 1:
            break
    t_limits = np.array(t_limits)
    if not do_dilate:
        return t_all, np.linspace(t_all[0], t_all[-1], 10), t_limits
    return np.array(dilated_time), np.array(tick_marks), t_limits
    

def plot_periods(ax_top, ax_bot,
                 args, times_and_periods_baseline,
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
    t_sec = t * 1e-9
    t0 = t_sec[0]
    t_offset = 0.0004043   # hack to switch to 125khz at t = 20.000255

    top_time, tick_locations, t_lim = dilate_time(
        t_sec - t0, t_offset, args.warp)
    L = L[0:top_time.shape[0]]

    ax_top.plot(top_time, L, 'o-', label=r'$\tilde{L}(t)$')
    ax_top.plot((top_time[0], top_time[-1]), (0, 0), '--', color='grey')
    ax_top.set_ylabel(r'$\tilde{L}(t)$')

    markersize = 4 if args.warp else 15

    # baseline
    bot_time, _, _ = dilate_time(times_on_off[:, 1] - t0,
                                 t_offset, args.warp)
    e = bot_time.shape[0]
    ax_bot.plot(bot_time, 1.0/(times_on_off[:e, 0] - times_on_off[:e, 1]), 'x',
                markersize=markersize,
                color='green', label='baseline')
    # filtered
    bot_time, _, _ = dilate_time(t_filtered[:, 1] - t0,
                                 t_offset, args.warp)
    e = bot_time.shape[0]
    ax_bot.plot(bot_time, 1.0/(t_filtered[:e, 0] - t_filtered[:e, 1]), '+',
                markersize=markersize,
                color='red', label='filtered')
    # interpolated
    bot_time, _, _ = dilate_time(t_interp[:, 1] - t0, t_offset, args.warp)

    e = bot_time.shape[0]
    ax_bot.plot(bot_time, 1.0/(t_interp[:e, 0] - t_interp[:e, 1]), 'o',
                markersize=markersize,
                markerfacecolor='none', color='black',label='interpolated')
    i_125  = len(freq_table) - 1

    if args.warp:
        gt_x_lim = ((17, 19), (16, 17), (19, 20))
    else:
        i = 16
        gt_x_lim = ((t_lim[i], t_lim[i + 2]),
                    (t_lim[i - 1], t_lim[i]),
                    (t_lim[i + 2], t_lim[i + 3]))

    ax_bot.plot(gt_x_lim[0], (freq_table[17], freq_table[17]), '--',
                color='violet', label='ground truth')
    ax_bot.plot(gt_x_lim[1], (freq_table[16], freq_table[16]), '--',
                color='violet')
    ax_bot.plot(gt_x_lim[2], (freq_table[16], freq_table[16]), '--',
                color='violet')
    ax_bot.set_yscale('log')
    ax_bot.set_ylabel('frequency [hz]')
    
    fontsize_legend = int(fontsize * 0.75)
    ax_bot.legend(loc='upper right', prop={'size': fontsize_legend})

    if args.warp:
        skip_ticks = 5  # 5 for full range
        tick_idx = list(range(0, len(tick_locations), skip_ticks)) \
            + [len(tick_locations) - 1]
        ax_bot.set_xticks(tick_idx)
        tick_marks = [f'{x:.3f}' for x in tick_locations[tick_idx]];
        ax_bot.set_xticklabels(tick_marks)
    else:
        x_start, x_end = t_lim[i_125 - 3], t_lim[i_125 + 3]
        ax_bot.get_xaxis().get_major_formatter().set_useOffset(False)
        ax_bot.set_xlim((x_start, x_end))
        ax_bot.xaxis.set_ticks(np.arange(np.round(x_start), x_end, 1e-4))
        
        #ax_bot.xaxis.set_major_formatter(ticker.FormatStrFormatter('%0.1f'))
    # set font size for title, axis labels and ticks
    set_font_size((ax_top, ax_bot), fontsize)


def make_graph(ax_top, ax_bot, args, data, res,
               cutoff_period, skip_plot, num_plot):
    if args.filter_pass_dt > 0:
        data = core_filtering.filter_noise(
            data, args.filter_pass_dt, args.filter_dead_dt)
    L = reconstruct(data, cutoff_period)
    plot_periods(ax_top, ax_bot, args,
                 find_periods_baseline(data, L, cutoff_period),
                 find_periods_filtered(data, L, cutoff_period), data,
                 skip_plot, num_plot)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='show different reconstruction methods.')
    parser.add_argument('--topic', '-t', action='store', default='/event_camera/events',
                        required=False, help='ros topic')
    parser.add_argument('--pixel', '-p', action='store', default=None,
                        required=True, type=int,
                        help='which pixel to plot')
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
    parser.add_argument('--warp', dest='warp', action='store_true',
                        help='warp time axis')
    parser.add_argument('--no-warp', dest='warp', action='store_false',
                        help="don't warp time axis")
    parser.set_defaults(warp=True)

    args = parser.parse_args()

    if args.filter_dead_dt is None:
        args.filter_dead_dt = args.filter_pass_dt

    cfg = read_yaml(args.config_file)
    fig, axs = plt.subplots(nrows=2*len(cfg['graphs']), ncols=1, sharex=True)
     
    for i, c in enumerate(cfg['graphs']):
        array, res = read_bag_ros2.read_as_array(
            bag_path=cfg['base_dir'] + '/' + c['bag'], topic=args.topic,
            use_sensor_time=True, skip=c['skip'],
            max_read=c['max_read'])
        make_graph(axs[2 * i], axs[2 * i + 1],
                   args, array[args.pixel], res,
                   cutoff_period=c['cutoff_period'],
                   skip_plot=c['skip_events_plot'], num_plot=c['num_events_plot'])
    #fig.tight_layout()
    if args.warp:
        plt.subplots_adjust(left=0.08, right=0.98, top=0.98, bottom=0.1,
                            hspace=0.1, wspace=0.04)
    else:
        plt.subplots_adjust(left=0.12, right=0.98, top=0.98, bottom=0.1,
                            hspace=0.1, wspace=0.04)
        
    axs[-1].set_xlabel('time [s]')

    plt.show()
