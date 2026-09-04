"""Optional Matplotlib figure for the fixed imperfect-evidence study."""
import csv
from pathlib import Path


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=Path(__file__).parent
    with (root/'results/robustness/summary.csv').open() as f:
        rows=list(csv.DictReader(f))
    scope=[r for r in rows if r['panel']=='scope' and
           tuple(float(r[k]) for k in ('evidence_accuracy','externality_rate','harm','scope_cost'))==(.95,.05,12,.1)]
    retry=[r for r in rows if r['left']=='verify_and_retry' and
           tuple(float(r[k]) for k in ('false_positive_rate','evidence_accuracy','accident_rate','verification_cost'))==(.05,.95,.25,.6)]
    scope.sort(key=lambda r:float(r['false_positive_rate']))
    retry.sort(key=lambda r:float(r['repair_cost']))
    fig,axes=plt.subplots(1,2,figsize=(12.5,6.4),facecolor='#faf9f6')
    for ax,data,key,title,xlabel in (
        (axes[0],scope,'false_positive_rate','Screening can become over-refusal','False-positive probability'),
        (axes[1],retry,'repair_cost','Retries must justify their cost','Retry cost (model units)')):
        xs=[float(r[key]) for r in data]
        ys=[float(r['mean_delta']) for r in data]
        lo=[float(r['mean_delta'])-float(r['ci_low']) for r in data]
        hi=[float(r['ci_high'])-float(r['mean_delta']) for r in data]
        ax.set_facecolor('#faf9f6')
        ax.axhline(0,color='#8a969d',lw=1)
        ax.plot(xs,[float(r['analytic_delta']) for r in data],'--',color='#a45d3b',lw=2,label='Analytic expectation')
        ax.errorbar(xs,ys,yerr=[lo,hi],fmt='o-',color='#23647a',lw=2,capsize=4,label='Simulation mean + 95% interval')
        ax.set_title(title,loc='left',fontsize=14,pad=16)
        ax.set_xlabel(xlabel,fontsize=11,labelpad=10)
        ax.set_ylabel('Social net difference per opportunity',fontsize=10)
        ax.spines[['top','right']].set_visible(False)
        ax.grid(axis='y',alpha=.15)
        ax.tick_params(labelsize=10)
    axes[0].text(.02,.05,'Scope screening minus naive trust\n5% harmful tasks; sensitivity 95%',transform=axes[0].transAxes,fontsize=10,color='#465764')
    axes[1].text(.02,.05,'Verify + retry minus verify only\n25% accidents; sensitivity 95%; 5% false positives',transform=axes[1].transAxes,fontsize=10,color='#465764')
    axes[0].legend(loc='upper right',fontsize=9,frameon=False)
    fig.text(.055,.94,'Cooperation mechanisms must earn their costs',fontsize=23,weight='bold',color='#18232b')
    fig.text(.055,.89,'Selected complete slices of a 540-cell synthetic sensitivity study',fontsize=12,color='#465764')
    fig.text(.055,.035,'20 paired seeds per cell. Bootstrap intervals are unadjusted and describe Monte Carlo variation only.\nNo real agents were evaluated; the full grid and model assumptions accompany this figure.',fontsize=10,color='#465764')
    fig.subplots_adjust(left=.07,right=.98,top=.79,bottom=.22,wspace=.27)
    fig.savefig(root/'results/robustness/comparison.png',dpi=150,metadata={'Software':'Coordination Repair Lab'})
    plt.close(fig)


if __name__=='__main__':
    main()
