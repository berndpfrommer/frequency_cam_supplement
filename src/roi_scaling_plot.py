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
import matplotlib.ticker as plticker

import argparse
import numpy as np
import read_bag_ros2
import yaml
import core_filtering


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def read_yaml(filename):
    with open(filename, 'r') as y:
        try:
            return yaml.safe_load(y)
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


def print_stats(periods, label):
    print(f"{label:15s}  mean: {periods.mean():10.7f} " +
          f"std: {periods.std():10.7f} ",
          f"min: {periods.min():10.7f} ",
          f"max: {periods.max():10.7f}")

    
def make_label(periods, label):
    return f'{label:13s}' + f'mean={periods.mean()*1000:.4f}ms' \
        + ' $\sigma=$' + f'{periods.std()*1000:.4f}ms'
    

def plot_periods(ax, args, times_and_periods_baseline,
                 times_and_periods_filtered, data, t_lim, config):
    """plot_pixel() plots pixel data"""
    gt = 1.0 / config['ground_truth']

    # if filter parameters are specified, apply high-noise filter
    times_off_on, periods_off_on, times_on_off, periods_on_off = \
        times_and_periods_baseline
    t_filtered, periods_filtered, t_interp, periods_interp = \
        times_and_periods_filtered[0]
    t, L = times_and_periods_filtered[1:3]
    mean = periods_on_off.mean()
    std = max(periods_on_off.std(), periods_filtered.std(), periods_interp.std())

    print_stats(periods_on_off, "OFF->OFF base")
    print_stats(periods_filtered, "filtered")
    print_stats(periods_interp, "interpolated")
    bins = np.linspace(max(0, mean - 3 * std), mean + 3 * std, 100)

    baseline_on_off, pb = np.histogram(periods_on_off, bins=bins)
    filtered, pb = np.histogram(periods_filtered, bins=bins)
    interp, pb = np.histogram(periods_interp, bins=bins)
    pb = 0.5 * (pb[:-1] + pb[1:])

    fontsize = 20
    fontsize_legend = int(fontsize * 0.75)

    # ---- histogram of periods
    lw = 3
    plot_error = False
    center = gt if plot_error else 0

    ax.step((pb - center) * 1e3, baseline_on_off,
            label=make_label(periods_on_off, 'baseline'),
            where='mid', linewidth=lw, color='green')
    ax.step((pb - center) * 1e3, filtered, '--',
            label=make_label(periods_filtered, 'filtered'),
            where='mid', linewidth=lw, color='red')
    ax.step((pb - center) * 1e3, interp,
            label=make_label(periods_interp, 'interpolated'),
            where='mid', linewidth=lw, color='black')

    ax.legend(loc='upper right', prop={'size': fontsize_legend,
                                       'family': 'monospace'})
    ax.set_ylabel('count')
    ax.set_title(config['title'])
    if config['show_x_axis_label']:
        err_str = "error " if plot_error else ""
        ax.set_xlabel(f'period {err_str}[ms]')
        ax.xaxis.set_major_locator(plticker.MultipleLocator(
            base=config['x_tick_spacing']))
        ax.xaxis.set_minor_locator(plticker.MultipleLocator(
            base=config['x_tick_spacing']*0.2))

    # set font size for title, axis labels and ticks
    set_font_size((ax, ), fontsize)


def plot_reconstruction(ax, args, data, L, t_lim, config):
    title = c['title']
    skip_plot = config['skip_plot']

    t = data[skip_plot:, 0] - data[skip_plot, 0]
    L_lim = L[skip_plot:][t < t_lim]
    t = t[t < t_lim]

    ax.plot(t * 1e-9, L_lim, '-o')
    ax.plot((t[0] * 1e-9, t[-1] * 1e-9), (0, 0), '-', color='black')
    ax.set_ylabel(r'$\tilde{L}(t)$')
    ax.set_title(title)

    if config['show_x_axis_label']:
        ax.set_xlabel(f'time [s]')
        maj_loc = plticker.MultipleLocator(
            base=config['x_tick_spacing'])
        ax.xaxis.set_major_locator(maj_loc)
        ax.xaxis.set_minor_locator(plticker.MultipleLocator(
            base=config['x_tick_spacing']*0.2))
    
    # set font size for title, axis labels and ticks
    fontsize = 20
    set_font_size((ax, ), fontsize)


def make_graph(ax, args, data, res, t_lim, config):
    """make graph comparing baseline with filter"""
    
    cutoff_period = config['cutoff_period']

    if args.filter_pass_dt > 0:
        data = core_filtering.filter_noise(
            data, args.filter_pass_dt, args.filter_dead_dt)
    L = core_filtering.reconstruct(data, cutoff_period)
    if args.show_reconstruction:
        plot_reconstruction(ax, args, data, L, t_lim, config)
    else:
        plot_periods(
            ax, args,
            core_filtering.find_periods_baseline(data, L, cutoff_period),
            core_filtering.find_periods_filtered(data, L, cutoff_period),
            data, t_lim, c)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='show how ROI affects frequency detection.')
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
    parser.add_argument("--show_reconstruction", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="show brightness reconstruction.")
    args = parser.parse_args()
    
    if args.filter_dead_dt is None:
        args.filter_dead_dt = args.filter_pass_dt

    cfg = read_yaml(args.config_file)
    fig, axs = plt.subplots(nrows=len(cfg['graphs']), ncols=1, sharex=True,)
    
    if not isinstance(axs, np.ndarray):
        axs = np.array([axs])
    
    arrays, res = [], []
    for ax, c in zip(axs, cfg['graphs']):
        print('reading events for pixel!')
        a, r = read_bag_ros2.read_events_for_pixels(
            bag_path=cfg['base_dir'] + '/' + c['bag'],
            pixel_list=[args.pixel],
            topic=args.topic,
            use_sensor_time=True, skip=c['skip_read'],
            max_read=c['max_read'])
        arrays.append(a)
        res.append(r)

    t_lim = np.min(np.array(
        [a[args.pixel][-1, 0]
         - a[args.pixel][cfg['graphs'][-1]['skip_plot'], 0]
         for a in arrays]))
    
    for ax, c, a, r in zip(axs, cfg['graphs'], arrays, res):
        make_graph(ax,  args, a[args.pixel], r, t_lim, c)

    #fig.tight_layout()
    plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1,
                        hspace=0.34, wspace=0.04)
    plt.show()
