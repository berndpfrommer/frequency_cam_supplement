#!/usr/bin/env python3
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
"""Plot filter transfer functions etc."""


import matplotlib.pyplot as plt
import argparse
import math
import numpy as np
import read_bag_ros2
import core_filtering


def compute_H_alpha_detrend_sq(omega, alpha):
    return  (2 - 2 * math.cos(omega)) / (1 - 2 * alpha * math.cos(omega) + alpha * alpha)


def compute_H_beta_norm_sq(omega, beta):
    return  (1 - beta)**2 / (1 + beta**2 - 2 * beta * np.cos(omega))


def compute_alpha_for_max(omega):
    co = math.cos(omega)
    alpha = 2 - co - math.sqrt(3 - 4 * co + co**2)
    return (alpha)


def compute_cos_omega_max(alpha, beta):
    a = alpha + 1 / alpha
    b = beta + 1 / beta
    cos_omega_max = 1 - math.sqrt(1 - 0.5 * a - 0.5 * b + 0.25 * a * b)
    return cos_omega_max


def compute_H_max_sq(alpha, beta):
    y = 2 * compute_cos_omega_max(alpha, beta)
    a = alpha + 1 / alpha
    b = beta + 1 / beta
    H_max_sq = (1 + beta)**2 / (4 * alpha * beta) * (2 - y) / ((y - a) * (y - b))
    return H_max_sq


def plot_filter(args):
    print('cutoff period: ', args.cutoff_period)
    alpha = core_filtering.compute_alpha_for_cutoff(args.cutoff_period)
    print('alpha: ', alpha)
    beta = core_filtering.compute_beta_for_cutoff(args.cutoff_period)
    #beta = args.beta
    print('beta: ', beta)
    omega_cut = 2 * np.pi / (args.cutoff_period
                             if args.cutoff_period else 2.0 / alpha)
    print('omega_cut / pi: ', omega_cut / np.pi)
    print('test for H_alpha at 0.5: ',
          compute_H_alpha_detrend_sq(omega_cut, alpha) /
          compute_H_alpha_detrend_sq(np.pi, alpha))
    omega = np.linspace(1e-4, np.pi, 100)
    z = np.exp(1.0j * omega)
    H_alpha = (z - 1) / (z - alpha)
    H_alpha_sq = np.real(H_alpha * np.conjugate(H_alpha))
    H_alpha_sq_max = 4 / (1 + alpha)**2
    H_beta = 0.5 * z * (1 + beta) / (z - beta)
    H_beta_n = 2 * (1 - beta) / (1 + beta)
    H_beta_norm = H_beta_n * H_beta
    H_beta_norm_sq = np.real(H_beta_norm * np.conjugate(H_beta_norm))
    H_ab = H_alpha * H_beta
    H_ab_sq = np.real(H_ab * np.conjugate(H_ab))
    H_ab_norm_sq = compute_H_max_sq(alpha, beta)
    _, axs = plt.subplots(1, 1)
    ia = 5
    iab = 3
    lw = 3
    fontsize = 40
    axs.plot(omega[ia:] / np.pi, 10 * np.log10(H_alpha_sq[ia:] / H_alpha_sq_max),
             '-', label=r'$|H_{\alpha}(\omega)|^2$', linewidth=lw)
    axs.plot(omega / np.pi, 10 * np.log10(H_beta_norm_sq), '-',
             label=r'$|H_{\beta}(\omega)|^2$', linewidth=lw)
    axs.plot(omega[iab:] / np.pi, 10 * np.log10(H_ab_sq[iab:] / H_ab_norm_sq),
             '-',  label=r'$|H(\omega)|^2$', linewidth=2*lw, color='k')
    axs.plot((omega_cut / np.pi, omega_cut / np.pi), (0, -12),
             '--', label=r'$\omega_{cut}$', linewidth=lw)
    axs.set_xlabel(r'$\omega/\pi$')
    axs.set_ylabel('dB')
    
    axs.legend(prop={'size': int(fontsize * 0.75)},
               loc='best', bbox_to_anchor=(0.79, 0.4))
    set_font_size((axs, ), fontsize)
    plt.subplots_adjust(left=0.13, right=0.98, top=0.97, bottom=0.15)

    plt.show()


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
    if args.filter_pass_dt > 0:
        data = core_filtering.filter_noise(
            data, args.filter_pass_dt, args.filter_dead_dt)
    num_on = np.count_nonzero(data[:, 1] > 0)
    num_off = max(data.shape[0] - num_on, 1)
    on_ratio = args.on_ratio if args.on_ratio else num_on / num_off
    dx = 2 * data[:, 1].astype(np.float) - 1
    dx_detrend = np.where(data[:, 1] == 1, 1, -on_ratio)
    x = np.cumsum(dx)
    x_detrend = np.cumsum(dx_detrend)
    num_graphs = 3
    fig, axs = plt.subplots(nrows=num_graphs, ncols=1, sharex=True,
                            gridspec_kw={'height_ratios': [1, 2, 2]})
    fontsize = 30
    fontsize_legend = int(fontsize * 0.55)
    t = (data[:, 0] - (data[0, 0] if args.t_at_zero else 0)) * 1e-9
    # ---- polarity
    axs[0].plot(t, dx, 'x', color='r', label='raw events')
    axs[0].yaxis.set_ticks((-1, 1))
    axs[0].set_ylabel('polarity')
    axs[0].set_ylim(-1.4, 1.4)
    axs[0].legend(loc='center right', prop={'size': fontsize_legend })

    # ---- naive integration
    axs[1].plot(t, x, 'o-', label='integrated: $C_{ON} = 1$, $C_{OFF} = 1$')
    axs[1].set_ylabel(r'$\tilde{L}(t)$')
    axs[1].legend(loc='lower right', prop={'size': fontsize_legend })
    # ---- detrended integration
    axs[2].plot(t, x_detrend, 'o-', label='integrated: $C_{ON}$ = 1, $C_{OFF}$ = ' +
                f'{on_ratio:.2f}')
    axs[2].set_ylabel(r'$\tilde{L}(t)$')
    axs[2].set_xlabel('time [s]')
    axs[2].legend(loc='lower right', prop={'size': fontsize_legend })
    # set font size for title, axis labels and ticks
    set_font_size(axs, fontsize)
    plt.subplots_adjust(left=0.13, right=0.98, top=0.97, bottom=0.1)
#    plt.tight_layout()
    print(fig)
    plt.show()

    
def filter_pixel(args, data):
    """filter_pixel() apply filter and plot data"""
    # if filter parameters are specified, apply high-noise filter
    if args.filter_pass_dt > 0:
        data = core_filtering.filter_noise(
            data, args.filter_pass_dt, args.filter_dead_dt)
    num_graphs = 1
    fig, axs = plt.subplots(nrows=num_graphs, ncols=1, sharex=True,
                            gridspec_kw={'height_ratios': [1]})
    axs = (axs, )
    fontsize = 40
    t = (data[:, 0] - (data[0, 0] if args.t_at_zero else 0)) * 1e-9
    for i, m in enumerate((0.5, 1.0, 2.0)):
        T = args.cutoff_period * m
        alpha = core_filtering.compute_alpha_for_cutoff(T)
        beta  = core_filtering.compute_beta_for_cutoff(T)
        # alpha = compute_alpha_for_max(2 * math.pi / T)
        # beta = alpha
        dx = np.where(data[:, 1] == 0, -1, 1)
        L = core_filtering.filter_iir(dx, alpha, beta, (0, 0))
        label = r'$T_{cut}=$' + f'{int(T):d}'
        axs[0].plot(t, L, 'o-', label=label, linewidth=4)
        axs[0].set_ylabel(r'$\tilde{L}(t)$')
    axs[-1].legend(loc='upper right', prop={'size': int(fontsize * 0.75) })
    axs[-1].plot((t[0], t[-1]), (0, 0), '-', color='k')
    axs[-1].set_xlabel('time [s]')
    plt.subplots_adjust(left=0.13, right=0.98, top=0.97, bottom=0.15)

    # set font size for title, axis labels and ticks
    set_font_size(axs, fontsize)
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


def apply_filter(args, array, res):
    """main function to apply filter to pixel signal"""
    active_pixels = [idx for idx, d in enumerate(array) if d.shape[0] > 0]
    print(active_pixels)
    print('number of active pixels: ', len(active_pixels))
    print('top active pixels: ', active_pixels[0:min(10, len(active_pixels))])
    for p in args.pixel:
        a = array[p]
        s = args.skip_events_plot
        n = min(s + args.num_events_plot, a.shape[0])
        filter_pixel(args, a[s:n, :])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='visualize how filter digital works.')
    parser.add_argument('--bag', '-b', action='store', default=None,
                        required=False, help='name of rosbag')
    parser.add_argument('--topic', '-t', action='store', default='/event_camera/events',
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

    parser.add_argument('--filter', action='store_true',
                        required=False, help='apply filter to signal')
    parser.set_defaults(filter=False)
    
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
    parser.add_argument('--cutoff_period',
                        action='store', default=None, type=float,
                        help='number of detrend events')
    parser.add_argument('--num_events_plot', '-n',
                        action='store', default=10000000000, type=int,
                        help='number of events to plot')
    parser.add_argument('--skip_events_plot', '-s',
                        action='store', default=0, type=int,
                        help='number of events to skip on plot')

    args = parser.parse_args()
    
    if args.bag is None:
        plot_filter(args)
    else:
        if len(args.pixel) == 0:
            raise Exception("must specify some pixels!")
        if args.filter_dead_dt is None:
            args.filter_dead_dt = args.filter_pass_dt
        if args.bag is None:
            raise Exception("must specify bag!")

        array, res = read_bag_ros2.read_as_array(
            args.bag, args.topic, use_sensor_time=True, skip=args.skip,
            max_read=args.max_read)
        if args.filter:
            apply_filter(args, array, res)
        else:
            plot_pixels(args, array, res)
    
