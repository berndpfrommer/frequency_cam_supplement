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
import matplotlib.ticker as ticker
import core_filtering


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


def find_periods(data):
    last_t = [None, None]
    last_p = None
    period = [[], []]
    times = [[], []]
    for d in data:
        t = d[0]
        p = d[1]
        if last_p is not None and last_p != p:
            if p:
                if last_t[0] is not None:
                    period[0].append(t - last_t[0])
                    times[0].append((last_t[0], t))
                last_t[0] = t
            else:
                if last_t[1] is not None:
                    period[1].append(t - last_t[1])
                    times[1].append((last_t[1], t))
                last_t[1] = t
        last_p = p
    return 1e-9 * np.array(times[0]), 1e-9 * np.array(period[0]), \
        1e-9 * np.array(times[1]), 1e-9 * np.array(period[1])


def draw_arrows(ax, t, all_too, label, level, fontsize, color):
    for too in all_too:
        if too[0] > t[0] and too[1] < t[-1]:
            ax.annotate("", xy=(too[1], level), xytext=(too[0], level),
                        arrowprops=dict(
                            arrowstyle="->, head_width=0.3, head_length=1.0",
                            lw=3.5,
                            color=color,
                            facecolor=color))
            ax.text(0.5 * (too[0] + too[1]), level + 0.15, label,
                    ha='center', fontsize=fontsize, color=color)


def plot_pixel(args, times_and_periods, data):
    """plot_pixel() plots pixel data"""
    # if filter parameters are specified, apply high-noise filter
    times_off_on, periods_off_on, times_on_off, periods_on_off = \
        times_and_periods
    mean = np.array([periods_off_on.mean(), periods_on_off.mean()]).mean()
    std = max(periods_off_on.std(), periods_on_off.std())
    # import pdb; pdb.set_trace()
    print("low end: ", np.sort(periods_off_on)[:20])
    print("high end: ", np.sort(periods_off_on)[-20:])
    print(f"ON  -> ON  period mean: {periods_off_on.mean()} " +
          f"std: {periods_off_on.std()} ",
          f"min: {periods_off_on.min()} ",
          f"max: {periods_off_on.max()}")

    print(f"OFF -> OFF period mean: {periods_on_off.mean()} " +
          f"std: {periods_on_off.std()} ",
          f"min: {periods_on_off.min()} ",
          f"max: {periods_on_off.max()}")
    bins = np.linspace(mean - std, mean + std, 200)
    naive_off_on, pb = np.histogram(periods_off_on, bins=bins)
    naive_on_off, pb = np.histogram(periods_on_off, bins=bins)
    pb = 0.5 * (pb[:-1] + pb[1:])

    num_graphs = 2
    fig, axs = plt.subplots(nrows=num_graphs, ncols=1, sharex=False,
                            gridspec_kw={'height_ratios': [1, 3]})
    fontsize = 30
    fontsize_legend = int(fontsize * 0.75)
    t = (data[:, 0] - (data[0, 0] if args.t_at_zero else 0)) * 1e-9
    dx = np.where(data[:, 1] == 0, -1, 1)

    # ---- polarity
    axs[0].plot(t-t[0], dx, 'x', color='r', label='event')
    axs[0].yaxis.set_ticks((-1, 1))
    axs[0].set_ylabel('polarity')
    axs[0].legend(loc='lower right', prop={'size': fontsize_legend})
    axs[0].set_xlabel('time [s]')
    axs[0].set_ylim(-1.4, 1.4)
    draw_arrows(axs[0], t - t[0], times_off_on - t[0], 'first ON to ON',
                0.4, fontsize * 0.7, color='blue')
    draw_arrows(axs[0], t - t[0], times_on_off - t[0], 'first OFF to OFF',
                -0.7, fontsize * 0.7, color='green')
    axs[0].xaxis.set_major_locator(ticker.MultipleLocator(1e-2))

    # ---- histogram of periods
    lw = 3
    axs[1].step(pb * 1e3, naive_off_on, label='first ON to ON event',
                where='mid', linewidth=lw, color='blue')
    axs[1].step(pb * 1e3, naive_on_off, label='first OFF to OFF event',
                where='mid', linewidth=lw, color='green')
    axs[1].legend(loc='upper right', prop={'size': fontsize_legend })
    axs[1].set_ylabel('count')
    axs[1].set_xlabel('period [ms]')
    # set font size for title, axis labels and ticks
    set_font_size(axs, fontsize)
    fig.tight_layout()
    plt.subplots_adjust(left=0.2, right=0.95, top=0.95, bottom=0.1,
                        hspace=0.34, wspace=0.04)
    plt.show()


def plot_pixels(args, array, res):
    """main function to plot pixels"""
    active_pixels = [idx for idx, d in enumerate(array) if d.shape[0] > 0]
    print(active_pixels)
    print('number of active pixels: ', len(active_pixels))
    print('top active pixels: ', active_pixels[0:min(10, len(active_pixels))])
    for p in args.pixel:
        data = array[p]
        if args.filter_pass_dt > 0:
            data = core_filtering.filter_noise(
                data, args.filter_pass_dt, args.filter_dead_dt)
        times_and_periods = find_periods(data)
        s = args.skip_events_plot
        n = min(s + args.num_events_plot, data.shape[0])
        plot_pixel(args, times_and_periods, data[s:n, ...])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='visualize how filter digital works.')
    parser.add_argument('--bag', '-b', action='store', default=None,
                        required=False, help='name of rosbag')
    parser.add_argument('--topic', '-t', action='store',
                        default='/event_camera/events',
                        required=False, help='ros topic')
    parser.add_argument('--pixel', '-p', action='append', default=[],
                        required=False, type=int,
                        help='which pixels to plot (usable multiple times)')
    parser.add_argument('--max_read', '-m', action='store', default=None,
                        required=False, type=int,
                        help='how many events to read (total)')
    parser.add_argument('--t_at_zero', '-0', action='store_true',
                        required=False, help='start time at zero')
    parser.set_defaults(t_at_zero=False)

    parser.add_argument('--filter_pass_dt', action='store', default=0e-6,
                        type=float, help='passing dt between OFF followed by ON')
    parser.add_argument('--filter_dead_dt', action='store',
                        default=None, type=float,
                        help='filter dt between event preceeding OFF/ON pair')
    parser.add_argument('--on_ratio', action='store',
                        default=None, type=float,
                        help='fraction of ON/OFF events for detrending')
    parser.add_argument('--skip', action='store', default=0, type=int,
                        help='number of events to skip on read')
    parser.add_argument('--num_events_plot', '-n',
                        action='store', default=10000000000, type=int,
                        help='number of events to plot')
    parser.add_argument('--skip_events_plot', '-s',
                        action='store', default=0, type=int,
                        help='number of events to skip on plot')

    args = parser.parse_args()
    
    if len(args.pixel) == 0:
        raise Exception("must specify some pixels!")
    if args.filter_dead_dt is None:
        args.filter_dead_dt = args.filter_pass_dt
    if args.bag is None:
        raise Exception("must specify bag!")

    array, res = read_bag_ros2.read_as_array(
        args.bag, args.topic, use_sensor_time=True, skip=args.skip,
        max_read=args.max_read)
    plot_pixels(args, array, res)
