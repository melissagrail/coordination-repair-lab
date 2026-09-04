"""Optional figure: requires matplotlib; the simulation itself has no dependencies."""
import csv
from pathlib import Path
import statistics


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import TwoSlopeNorm
    root = Path(__file__).parent
    with (root / 'results/runs.csv').open() as f:
        rows = list(csv.DictReader(f))
    scenarios = list(dict.fromkeys(r['scenario'] for r in rows))
    policies = list(dict.fromkeys(r['policy'] for r in rows))
    values = [[statistics.fmean(float(r['social_net_per_opportunity']) for r in rows
                               if r['scenario'] == s and r['policy'] == p)
               for s in scenarios] for p in policies]
    fig, ax = plt.subplots(figsize=(13, 7.4), facecolor='#faf9f6')
    ax.set_facecolor('#faf9f6')
    im = ax.imshow(values, cmap='RdBu', norm=TwoSlopeNorm(vmin=-1, vcenter=0, vmax=4), aspect='auto')
    for i, row in enumerate(values):
        for j, value in enumerate(row):
            ax.text(j, i, f'{value:.2f}', ha='center', va='center', fontsize=11,
                    color='white' if value > 2.6 or value < -.7 else '#18232b')
    ax.set_xticks(range(len(scenarios)), [s.replace('_', '\n') for s in scenarios], fontsize=10)
    ax.set_yticks(range(len(policies)), [p.replace('_', ' ') for p in policies], fontsize=11)
    ax.tick_params(length=0, pad=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(.03, .95, 'Coordination Repair Lab', fontsize=24, weight='bold', color='#18232b')
    fig.text(.03, .905, 'Mean social net per opportunity · 40 paired seeds · higher is better', fontsize=13, color='#465764')
    fig.text(.03, .04, 'Synthetic fixed-rule model. Rankings depend on assumptions; this does not establish agent alignment.\nCosts to nonparticipants are included. Full accounting and paired intervals accompany the data.', fontsize=10, color='#465764')
    fig.colorbar(im, ax=ax, shrink=.75, pad=.025, label='Arbitrary model units')
    fig.subplots_adjust(left=.21, right=.94, top=.85, bottom=.19)
    fig.savefig(root / 'results/comparison.png', dpi=150, facecolor=fig.get_facecolor(), metadata={'Software':'Coordination Repair Lab'})
    plt.close(fig)


if __name__ == '__main__':
    main()
