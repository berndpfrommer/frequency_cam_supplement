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


def plot_pixel(args, data):
    """plot_pixel() plots pixel data"""
    # if filter parameters are specified, apply high-noise filter
    filt = core_filtering.filter_noise(
        data, args.filter_pass_dt, args.filter_dead_dt)
    
    num_on = np.count_nonzero(data[:, 1] > 0)
    num_off = max(data.shape[0] - num_on, 1)
    on_ratio = args.on_ratio if args.on_ratio else num_on / num_off
    dx = 2 * data[:, 1].astype(np.float) - 1
    dx_detrend = np.where(data[:, 1] == 1, 1, -on_ratio)
    x = np.cumsum(dx)
    x_detrend = np.cumsum(dx_detrend)

    dx_filt_detrend = np.where(filt[:, 1] == 1, 1, -on_ratio)
    x_filt_detrend = np.cumsum(dx_filt_detrend)

    num_graphs = 3 if args.show_filtered else 2
    fig, axs = plt.subplots(nrows=num_graphs, ncols=1, sharex=True,
                            gridspec_kw={
                                'height_ratios': [1] + [2] * (num_graphs - 1)})
    fontsize = 30
    fontsize_legend = int(fontsize * 0.55)
    t = (data[:, 0] - (data[0, 0] if args.t_at_zero else 0)) * 1e-9
    t_filt = (filt[:, 0] - (data[0, 0] if args.t_at_zero else 0)) * 1e-9
    # ---- polarity
    axs[0].plot(t, dx, 'x', color='r', label='raw events')
    axs[0].yaxis.set_ticks((-1, 1))
    axs[0].set_ylabel('polarity')
    axs[0].set_ylim(-1.4, 1.4)
    axs[0].legend(loc='center right', prop={'size': fontsize_legend })

    # ---- unfiltered
    axs[1].plot(t, x_detrend, 'o-', label='unfiltered')
    axs[1].set_ylabel(r'$\tilde{L}(t)$')
    axs[1].legend(loc='best', prop={'size': fontsize_legend })
    # ---- filtered
    if args.show_filtered:
        axs[2].plot(t_filt, x_filt_detrend, 'o-', label='filtered')
        axs[2].set_ylabel(r'$\tilde{L}(t)$')
        axs[2].legend(loc='lower right', prop={'size': fontsize_legend })
        axs[2].set_xlabel('time [s]')
        # set font size for title, axis labels and ticks
    else:
        axs[1].set_xlabel('time [s]')
        
    set_font_size(axs, fontsize)
    plt.subplots_adjust(left=0.13, right=0.98, top=0.97, bottom=0.1)
    plt.show()


def plot_pixels(args, array, res):
    """main function to plot pixels"""
    active_pixels = [idx for idx, d in enumerate(array) if d.shape[0] > 0]
    print(active_pixels)
    print('number of active pixels: ', len(active_pixels))
    print('top active pixels: ', active_pixels[0:min(10, len(active_pixels))])
    for p in args.pixel:
        a = array[p]
        s = args.skip_events_plot
        n = min(s + args.num_events_plot, a.shape[0])
        plot_pixel(args, a[s:n, ...])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='visualize how dark noise filter works.')
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

    parser.add_argument('--filter_pass_dt', action='store', default=1.5e-6,
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
    parser.add_argument('--show_filtered', action='store_true',
                        required=False, help='show filtered data')
    parser.set_defaults(show_filtered=False)

    args = parser.parse_args()
    
    if len(args.pixel) == 0:
        raise Exception("must specify some pixels!")
    if args.bag is None:
        raise Exception("must specify bag!")
    if args.filter_dead_dt is None:
        args.filter_dead_dt = args.filter_pass_dt
    array, res = read_bag_ros2.read_as_array(
        args.bag, args.topic, use_sensor_time=True, skip=args.skip,
        max_read=args.max_read)
    plot_pixels(args, array, res)
    
