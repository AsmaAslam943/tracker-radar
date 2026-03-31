
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

owners = [
    ("Google",          47.4),
    ("Facebook",        14.0),
    ("LinkedIn",        13.5),
    ("Microsoft",       11.9),
    ("OneTrust",        11.8),
    ("AppNexus",        11.4),
    ("Adobe",           10.7),
    ("Trade Desk",      10.3),
    ("Rubicon Project", 10.2),
    ("Index Exchange",   9.0),
    ("LiveRamp",         7.9),
    ("PubMatic",         7.6),
    ("Amazon",           7.0),
    ("Criteo",           6.3),
    ("Comscore",         5.6),
    ("Outbrain",         4.6),
    ("Taboola",          4.5),
    ("Hotjar",           2.8),
]

owners_sorted = sorted(owners, key=lambda x: x[1])
labels = [o[0] for o in owners_sorted]
values = [o[1] for o in owners_sorted]

fig, ax = plt.subplots(figsize=(9, 8))
fig.patch.set_facecolor("white")
bars = ax.barh(labels, values, color="#4A8FD4", edgecolor="white", height=0.7)

for bar, val in zip(bars, values):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f"{val}%", va="center", fontsize=9, color="#444")

ax.set_xlabel("% of Top-1000 Websites", fontsize=11)
ax.set_title("Source of the Most Common Trackers\nFound on the Top 1000 Sites",
             fontsize=13, fontweight="bold", pad=15)
ax.set_xlim(0, 55)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))
ax.grid(axis="x", color="#e0e0e0", linewidth=0.8)
ax.set_axisbelow(True)

plt.tight_layout()
fig.savefig("results/figures/tracked.png", dpi=180, bbox_inches="tight")
print("Saved to results/figures/tracked.png")
