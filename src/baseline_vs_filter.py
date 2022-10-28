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
    return f'{label:12s}' + r' $\sigma=$' + f'{periods.std()*1000:.4f} ms'
    

def plot_periods(ax, args, times_and_periods_baseline,
                 times_and_periods_filtered, gt, data):
    """plot_pixel() plots pixel data"""
    # if filter parameters are specified, apply high-noise filter
    times_off_on, periods_off_on, times_on_off, periods_on_off = \
        times_and_periods_baseline
    t_filtered, periods_filtered, t_interp, periods_interp = \
        times_and_periods_filtered[0]
    t, L = times_and_periods_filtered[1:3]
    mean = np.array([periods_off_on.mean(), periods_on_off.mean()]).mean()
    std = max(periods_on_off.std(), periods_filtered.std(), periods_interp.std())
    #print_stats(periods_off_on, "ON->ON base")
    print_stats(periods_on_off, "OFF->OFF base")
    print_stats(periods_filtered, "filtered")
    print_stats(periods_interp, "interpolated")
    bins = np.linspace(mean - 3 * std, mean + 3 * std, 100)
    baseline_off_on, pb = np.histogram(periods_off_on, bins=bins)
    baseline_on_off, pb = np.histogram(periods_on_off, bins=bins)
    filtered, pb = np.histogram(periods_filtered, bins=bins)
    interp, pb = np.histogram(periods_interp, bins=bins)
    pb = 0.5 * (pb[:-1] + pb[1:])

    fontsize = 20
    fontsize_legend = int(fontsize * 0.75)

    # ---- histogram of periods
    lw = 3
    ax.step((pb - gt) * 1e3, baseline_on_off,
            label=make_label(periods_on_off, 'baseline'),
            where='mid', linewidth=lw, color='green')
    ax.step((pb - gt) * 1e3, filtered, '--',
            label=make_label(periods_filtered, 'filtered'),
            where='mid', linewidth=lw, color='red')
    ax.step((pb - gt) * 1e3, interp,
            label=make_label(periods_interp, 'interpolated'),
            where='mid', linewidth=lw, color='black')

    ax.legend(loc='upper right', prop={'size': fontsize_legend,
                                       'family': 'monospace'})
    ax.set_ylabel('count')
    ax.set_xlabel(f'period error [ms] at {round(1/gt):d} Hz')
    # set font size for title, axis labels and ticks
    set_font_size(axs, fontsize)


def make_graph(ax, args, data, res, cutoff_period, gt):
    """make graph comparing baseline with filter"""
    if args.filter_pass_dt > 0:
        data = core_filtering.filter_noise(
            data, args.filter_pass_dt, args.filter_dead_dt)
    L = core_filtering.reconstruct(data, cutoff_period)
    plot_periods(
        ax, args,
        core_filtering.find_periods_baseline(data, L, cutoff_period),
        core_filtering.find_periods_filtered(data, L, cutoff_period), gt, data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='show baseline vs filter performance.')
    parser.add_argument('--topic', '-t', action='store',
                        default='/event_camera/events',
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
    args = parser.parse_args()
    
    if args.filter_dead_dt is None:
        args.filter_dead_dt = args.filter_pass_dt

    cfg = read_yaml(args.config_file)
    fig, axs = plt.subplots(nrows=len(cfg['graphs']), ncols=1, sharex=False,)

    for ax, c in zip(axs, cfg['graphs']):
        array, res = read_bag_ros2.read_as_array(
            bag_path=cfg['base_dir'] + '/' + c['bag'], topic=args.topic,
            use_sensor_time=True, skip=c['skip'],
            max_read=c['max_read'])
        make_graph(ax,  args, array[args.pixel], res,
                   cutoff_period=c['cutoff_period'],gt=c['ground_truth'])
                            
    #fig.tight_layout()
    plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1,
                        hspace=0.34, wspace=0.04)
    plt.show()
